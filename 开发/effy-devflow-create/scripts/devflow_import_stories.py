#!/usr/bin/env python3
"""Import Story/Task breakdown markdown into Effy Devflow.

Defaults to dry-run. Use --execute to create missing stories/tasks.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://zxqijing.com/admin-api"
DEFAULT_PROJECT_ID = 3
DEFAULT_SPRINT_ID = 8
DEFAULT_TENANT_ID = "1"
DEFAULT_WORKFLOW_TEMPLATE_NAME = "软件开发流程"
DEFAULT_ASSIGNEE_NICKNAME = "胡广豪"
DEFAULT_STORY_TYPE = 1
DEFAULT_STORY_MODULE = 1
DEFAULT_STORY_STATUS = 1
DEFAULT_TASK_TYPE = 1
DEFAULT_TASK_STATUS = 1
DEFAULT_PRIORITY = 2


@dataclass
class TaskSpec:
    number: str
    title: str
    body: str
    developer: str | None = None


@dataclass
class StorySpec:
    number: str
    title: str
    body: str
    tasks: list[TaskSpec] = field(default_factory=list)


class DevflowError(RuntimeError):
    pass


def now_slug() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def strip_heading_number(title: str) -> str:
    return title.strip().strip()


def parse_specs(path: Path) -> list[StorySpec]:
    text = path.read_text(encoding="utf-8")
    schedule_developers = parse_schedule_developers(text)
    story_matches = list(re.finditer(r"^## Story\s+(\d+)[：:]\s*(.+)$", text, re.M))
    stories: list[StorySpec] = []
    for index, match in enumerate(story_matches):
        start = match.end()
        end = story_matches[index + 1].start() if index + 1 < len(story_matches) else len(text)
        section = text[start:end].strip()
        task_matches = list(re.finditer(r"^### Task\s+([\d.]+)[：:]\s*(.+)$", section, re.M))
        story_body = section[: task_matches[0].start()].strip() if task_matches else section
        story = StorySpec(
            number=match.group(1),
            title=strip_heading_number(match.group(2)),
            body=story_body,
        )
        for task_index, task_match in enumerate(task_matches):
            task_start = task_match.end()
            task_end = (
                task_matches[task_index + 1].start()
                if task_index + 1 < len(task_matches)
                else len(section)
            )
            number = task_match.group(1)
            title = strip_heading_number(task_match.group(2))
            story.tasks.append(
                TaskSpec(
                    number=number,
                    title=title,
                    body=section[task_start:task_end].strip(),
                    developer=schedule_developers.get(number),
                )
            )
        stories.append(story)
    if not stories:
        raise DevflowError(f"No Story sections found in {path}")
    return stories


def parse_schedule_developers(text: str) -> dict[str, str]:
    developers: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("| Story "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        task_cell = cells[1]
        developer = cells[3]
        match = re.search(r"Task\s+([\d.]+)[：:]", task_cell)
        if match and developer and developer != "---":
            developers[match.group(1)] = developer
    return developers


def extract_chrome_token() -> str | None:
    profile_root = Path.home() / "Library/Application Support/Google/Chrome"
    candidates: list[tuple[int, str]] = []
    for profile in ("Profile 5", "Default"):
        leveldb = profile_root / profile / "Local Storage/leveldb"
        if not leveldb.exists():
            continue
        for file_path in leveldb.iterdir():
            if file_path.suffix not in {".ldb", ".log"}:
                continue
            try:
                text = file_path.read_bytes().decode("latin1", "ignore")
            except OSError:
                continue
            if "zxqijing.com" not in text:
                continue
            pattern = re.compile(
                r"ACCESS_TOKEN(?:S)?[^\{]{0,80}"
                r"\{\"c\":(\d+),\"e\":\d+,\"v\":\"\\?\"([0-9a-f]{32})\\?\"\"\}"
            )
            for match in pattern.finditer(text):
                candidates.append((int(match.group(1)), match.group(2)))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


class DevflowClient:
    def __init__(self, token: str, base_url: str, tenant_id: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.tenant_id = tenant_id

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        body = None if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=body, method=method)
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("tenant-id", self.tenant_id)
        request.add_header("Accept", "application/json")
        request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            raise DevflowError(f"{method} {path} HTTP {exc.code}: {raw}") from exc
        except urllib.error.URLError as exc:
            raise DevflowError(f"{method} {path} failed: {exc}") from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DevflowError(f"{method} {path} returned non-JSON: {raw[:300]}") from exc
        code = payload.get("code")
        if code not in (0, "0", 200, "200"):
            raise DevflowError(f"{method} {path} returned code={code}: {payload.get('msg')}")
        return payload.get("data")

    def get_workflow_template(self, project_id: int, name: str) -> dict[str, Any]:
        data = self.request(
            "GET",
            "/devflow/workflow-template/page",
            params={"pageNo": 1, "pageSize": -1, "status": 0, "projectId": project_id},
        )
        templates = data.get("list") or []
        for template in templates:
            if template.get("name") == name:
                return template
        names = ", ".join(str(template.get("name")) for template in templates)
        raise DevflowError(f"Workflow template {name!r} not found. Available: {names}")

    def get_users(self) -> list[dict[str, Any]]:
        return self.request("GET", "/system/user/simple-list") or []

    def get_project_board(self, project_id: int, sprint_id: int) -> list[dict[str, Any]]:
        data = self.request(
            "GET",
            "/devflow/project/board",
            params={"projectId": project_id, "sprintId": sprint_id},
        )
        return data.get("stories") or []

    def get_story_page(self, project_id: int, sprint_id: int) -> list[dict[str, Any]]:
        data = self.request(
            "GET",
            "/devflow/story/page",
            params={"pageNo": 1, "pageSize": -1, "projectId": project_id, "sprintId": sprint_id},
        )
        return data.get("list") or []

    def get_task_page(self, project_id: int, sprint_id: int) -> list[dict[str, Any]]:
        data = self.request(
            "GET",
            "/devflow/task/page",
            params={"pageNo": 1, "pageSize": -1, "projectId": project_id, "sprintId": sprint_id},
        )
        return data.get("list") or []

    def create_story(self, payload: dict[str, Any]) -> int:
        return int(self.request("POST", "/devflow/story/create", data=payload))

    def create_task(self, payload: dict[str, Any]) -> int:
        return int(self.request("POST", "/devflow/task/create", data=payload))

    def update_workflow(self, payload: dict[str, Any]) -> Any:
        return self.request("POST", "/devflow/task/update-workflow", data=payload)


def markdown_for_story(story: StorySpec) -> str:
    return f"## Story {story.number}: {story.title}\n\n{story.body}".strip()


def markdown_for_task(task: TaskSpec) -> str:
    return f"### Task {task.number}: {task.title}\n\n{task.body}".strip()


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip()).casefold()


def next_order_index(items: list[dict[str, Any]]) -> int:
    if not items:
        return 1000
    return int(max(item.get("orderIndex") or 0 for item in items) + 1000)


def build_workflow_node_updates(template: dict[str, Any], assignee_id: int | None) -> list[dict[str, Any]]:
    nodes = sorted(template.get("nodes") or [], key=lambda node: node.get("seqNo") or 0)
    if not nodes:
        return []
    first = nodes[0]
    update: dict[str, Any] = {"templateNodeId": first.get("id"), "bizStatus": 1}
    if assignee_id:
        update["assigneeUserId"] = assignee_id
    return [update]


def verify_specs(
    stories: list[StorySpec],
    existing_stories: list[dict[str, Any]],
    existing_tasks: list[dict[str, Any]],
    workflow_template_id: int,
) -> dict[str, Any]:
    story_by_title = {normalize_title(story.get("title") or ""): story for story in existing_stories}
    tasks_by_story_title: dict[int, dict[str, dict[str, Any]]] = {}
    for task in existing_tasks:
        story_id = int(task.get("storyId") or 0)
        tasks_by_story_title.setdefault(story_id, {})[normalize_title(task.get("title") or "")] = task

    missing_stories: list[dict[str, str]] = []
    missing_tasks: list[dict[str, str]] = []
    matched_story_ids: list[int] = []
    matched_task_ids: list[int] = []
    workflow_bad: list[dict[str, Any]] = []

    for story in stories:
        existing_story = story_by_title.get(normalize_title(story.title))
        if not existing_story:
            missing_stories.append({"number": story.number, "title": story.title})
            for task in story.tasks:
                missing_tasks.append(
                    {"story": story.title, "number": task.number, "title": task.title}
                )
            continue

        story_id = int(existing_story["id"])
        matched_story_ids.append(story_id)
        current_tasks = tasks_by_story_title.get(story_id, {})
        for task in story.tasks:
            existing_task = current_tasks.get(normalize_title(task.title))
            if not existing_task:
                missing_tasks.append(
                    {"story": story.title, "number": task.number, "title": task.title}
                )
                continue
            task_id = int(existing_task["id"])
            matched_task_ids.append(task_id)
            if (
                not existing_task.get("workflowEnabled")
                or int(existing_task.get("workflowTemplateId") or 0) != workflow_template_id
            ):
                workflow_bad.append(
                    {
                        "id": task_id,
                        "story": story.title,
                        "title": task.title,
                        "workflowEnabled": existing_task.get("workflowEnabled"),
                        "workflowTemplateId": existing_task.get("workflowTemplateId"),
                        "workflowStatus": existing_task.get("workflowStatus"),
                    }
                )

    return {
        "expectedStories": len(stories),
        "expectedTasks": sum(len(story.tasks) for story in stories),
        "matchedStories": len(matched_story_ids),
        "matchedTasks": len(matched_task_ids),
        "matchedStoryIds": matched_story_ids,
        "matchedTaskIds": matched_task_ids,
        "missingStories": missing_stories,
        "missingTasks": missing_tasks,
        "workflowBad": workflow_bad,
        "ok": not missing_stories and not missing_tasks and not workflow_bad,
    }


def run(args: argparse.Namespace) -> int:
    spec_path = Path(args.spec)
    stories = parse_specs(spec_path)
    if args.max_stories is not None:
        stories = stories[: args.max_stories]
    if args.max_tasks is not None:
        remaining = args.max_tasks
        limited_stories: list[StorySpec] = []
        for story in stories:
            if remaining <= 0:
                break
            limited = StorySpec(story.number, story.title, story.body)
            limited.tasks = story.tasks[:remaining]
            remaining -= len(limited.tasks)
            limited_stories.append(limited)
        stories = limited_stories

    if not args.execute and not args.verify_only:
        log: dict[str, Any] = {
            "startedAt": dt.datetime.now().isoformat(),
            "execute": False,
            "verifyOnly": False,
            "spec": str(spec_path),
            "projectId": args.project_id,
            "sprintId": args.sprint_id,
            "workflowTemplate": {"name": args.workflow_template},
            "defaultAssignee": {"nickname": args.default_assignee},
            "stories": [
                {
                    "number": story.number,
                    "title": story.title,
                    "tasks": [
                        {
                            "number": task.number,
                            "title": task.title,
                            "developer": task.developer,
                        }
                        for task in story.tasks
                    ],
                }
                for story in stories
            ],
            "summary": {
                "parsedStories": len(stories),
                "parsedTasks": sum(len(story.tasks) for story in stories),
                "createdStories": 0,
                "createdTasks": 0,
                "skippedStories": 0,
                "skippedTasks": 0,
                "createdStoryIds": [],
                "createdTaskIds": [],
            },
        }
        log_dir = Path(args.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"devflow-import-{now_slug()}-dry-run.json"
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"log": str(log_path), "summary": log["summary"]}, ensure_ascii=False, indent=2))
        return 0

    token = args.token or os.environ.get("DEVFLOW_TOKEN") or extract_chrome_token()
    if not token:
        raise DevflowError("No token found. Set DEVFLOW_TOKEN or log in to zxqijing.com in Chrome.")

    project_id = args.project_id
    sprint_id = args.sprint_id
    client = DevflowClient(token=token, base_url=args.base_url, tenant_id=args.tenant_id)
    workflow_template = client.get_workflow_template(project_id, args.workflow_template)
    users = client.get_users()
    user_by_nickname = {user.get("nickname"): user for user in users}
    default_assignee = user_by_nickname.get(args.default_assignee)
    if not default_assignee:
        raise DevflowError(f"Default assignee {args.default_assignee!r} was not found")
    assignee_id = int(default_assignee["id"])

    existing_stories = client.get_story_page(project_id, sprint_id)
    existing_tasks = client.get_task_page(project_id, sprint_id)
    story_by_title = {normalize_title(story.get("title") or ""): story for story in existing_stories}
    tasks_by_story_title: dict[int, dict[str, dict[str, Any]]] = {}
    for task in existing_tasks:
        story_id = int(task.get("storyId") or 0)
        tasks_by_story_title.setdefault(story_id, {})[normalize_title(task.get("title") or "")] = task

    log: dict[str, Any] = {
        "startedAt": dt.datetime.now().isoformat(),
        "execute": args.execute,
        "verifyOnly": args.verify_only,
        "spec": str(spec_path),
        "projectId": project_id,
        "sprintId": sprint_id,
        "workflowTemplate": {"id": workflow_template.get("id"), "name": workflow_template.get("name")},
        "defaultAssignee": {"id": assignee_id, "nickname": args.default_assignee},
        "stories": [],
    }

    if args.verify_only:
        log["verification"] = verify_specs(
            stories,
            existing_stories,
            existing_tasks,
            int(workflow_template["id"]),
        )
        log["summary"] = {
            "parsedStories": len(stories),
            "parsedTasks": sum(len(story.tasks) for story in stories),
            "createdStories": 0,
            "createdTasks": 0,
            "skippedStories": 0,
            "skippedTasks": 0,
            "createdStoryIds": [],
            "createdTaskIds": [],
        }
        log_dir = Path(args.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"devflow-import-{now_slug()}-verify.json"
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {"log": str(log_path), "summary": log["summary"], "verification": log["verification"]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if log["verification"]["ok"] else 2

    story_order_index = next_order_index(existing_stories)
    created_story_ids: list[int] = []
    created_task_ids: list[int] = []
    skipped_story_count = 0
    skipped_task_count = 0

    for story in stories:
        story_key = normalize_title(story.title)
        existing_story = story_by_title.get(story_key)
        story_log: dict[str, Any] = {"number": story.number, "title": story.title, "tasks": []}
        if existing_story:
            story_id = int(existing_story["id"])
            skipped_story_count += 1
            story_log.update({"action": "skip-existing", "id": story_id})
        else:
            story_payload = {
                "projectId": project_id,
                "sprintId": sprint_id,
                "title": story.title,
                "contentText": markdown_for_story(story),
                "type": DEFAULT_STORY_TYPE,
                "module": DEFAULT_STORY_MODULE,
                "status": DEFAULT_STORY_STATUS,
                "priority": DEFAULT_PRIORITY,
                "orderIndex": story_order_index,
            }
            story_log["payload"] = story_payload
            if args.execute:
                story_id = client.create_story(story_payload)
                story_by_title[story_key] = {"id": story_id, **story_payload}
                created_story_ids.append(story_id)
                time.sleep(args.delay)
            else:
                story_id = -len(log["stories"]) - 1
            story_order_index += 1000
            story_log.update({"action": "create", "id": story_id})

        current_story_tasks = tasks_by_story_title.setdefault(story_id, {})
        task_order_index = next_order_index(list(current_story_tasks.values()))
        for task in story.tasks:
            task_key = normalize_title(task.title)
            task_log: dict[str, Any] = {
                "number": task.number,
                "title": task.title,
                "developer": task.developer,
            }
            if task_key in current_story_tasks:
                skipped_task_count += 1
                task_log.update(
                    {
                        "action": "skip-existing",
                        "id": int(current_story_tasks[task_key].get("id")),
                    }
                )
                story_log["tasks"].append(task_log)
                continue

            task_assignee_id = assignee_id if (task.developer or args.default_assignee) else None
            task_payload = {
                "projectId": project_id,
                "sprintId": sprint_id,
                "storyId": story_id,
                "title": task.title,
                "contentText": markdown_for_task(task),
                "type": DEFAULT_TASK_TYPE,
                "status": DEFAULT_TASK_STATUS,
                "priority": DEFAULT_PRIORITY,
                "orderIndex": task_order_index,
                "assigneeUserId": task_assignee_id,
                "workflowTemplateId": workflow_template["id"],
            }
            workflow_payload_preview = {
                "workflowAction": "NONE",
                "nodeUpdates": build_workflow_node_updates(workflow_template, task_assignee_id),
            }
            task_log["payload"] = task_payload
            task_log["workflowPayloadPreview"] = workflow_payload_preview
            if args.execute:
                task_id = client.create_task(task_payload)
                workflow_payload = {"taskId": task_id, **workflow_payload_preview}
                if workflow_payload["nodeUpdates"]:
                    client.update_workflow(workflow_payload)
                created_task_ids.append(task_id)
                current_story_tasks[task_key] = {"id": task_id, **task_payload}
                task_log["workflowPayload"] = workflow_payload
                time.sleep(args.delay)
            else:
                task_id = -len(created_task_ids) - 1
            task_order_index += 1000
            task_log.update({"action": "create", "id": task_id})
            story_log["tasks"].append(task_log)
        log["stories"].append(story_log)

    log["summary"] = {
        "parsedStories": len(stories),
        "parsedTasks": sum(len(story.tasks) for story in stories),
        "createdStories": len(created_story_ids),
        "createdTasks": len(created_task_ids),
        "skippedStories": skipped_story_count,
        "skippedTasks": skipped_task_count,
        "createdStoryIds": created_story_ids,
        "createdTaskIds": created_task_ids,
    }
    if args.execute:
        refreshed_stories = client.get_story_page(project_id, sprint_id)
        refreshed_tasks = client.get_task_page(project_id, sprint_id)
        refreshed_task_ids = {int(task["id"]) for task in refreshed_tasks if task.get("id")}
        log["verification"] = {
            "storyPageCount": len(refreshed_stories),
            "taskPageCount": len(refreshed_tasks),
            "createdTasksPresent": all(task_id in refreshed_task_ids for task_id in created_task_ids),
        }

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    mode = "execute" if args.execute else "dry-run"
    log_path = log_dir / f"devflow-import-{now_slug()}-{mode}.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"log": str(log_path), "summary": log["summary"]}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spec",
        default="docs/superpowers/specs/2026-05-07-membership-prepaid-card-next-stories.md",
    )
    parser.add_argument("--execute", action="store_true", help="Create missing records in Devflow")
    parser.add_argument("--verify-only", action="store_true", help="Verify parsed records already exist")
    parser.add_argument("--token", help="Devflow access token. Defaults to DEVFLOW_TOKEN or Chrome storage.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--tenant-id", default=DEFAULT_TENANT_ID)
    parser.add_argument("--project-id", type=int, default=DEFAULT_PROJECT_ID)
    parser.add_argument("--sprint-id", type=int, default=DEFAULT_SPRINT_ID)
    parser.add_argument("--workflow-template", default=DEFAULT_WORKFLOW_TEMPLATE_NAME)
    parser.add_argument("--default-assignee", default=DEFAULT_ASSIGNEE_NICKNAME)
    parser.add_argument("--log-dir", default="docs/superpowers/logs")
    parser.add_argument("--delay", type=float, default=0.08)
    parser.add_argument("--max-stories", type=int, help="Only process the first N parsed stories")
    parser.add_argument("--max-tasks", type=int, help="Only process the first N parsed tasks")
    args = parser.parse_args()
    try:
        return run(args)
    except DevflowError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
