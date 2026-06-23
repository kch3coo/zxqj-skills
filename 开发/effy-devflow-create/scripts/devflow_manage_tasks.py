#!/usr/bin/env python3
"""Manage Effy Devflow tasks under an existing Story.

Defaults to dry-run. Use --execute to delete/create/update records.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from devflow_import_stories import (  # noqa: E402
    DEFAULT_BASE_URL,
    DEFAULT_PRIORITY,
    DEFAULT_TASK_STATUS,
    DEFAULT_TASK_TYPE,
    DEFAULT_TENANT_ID,
    DEFAULT_WORKFLOW_TEMPLATE_NAME,
    DevflowClient,
    DevflowError,
    extract_chrome_token,
    next_order_index,
    normalize_title,
    now_slug,
)


@dataclass(frozen=True)
class TaskInput:
    title: str
    body: str


@dataclass(frozen=True)
class CreatePlanItem:
    spec: TaskInput
    payload: dict[str, Any]
    workflow_payload: dict[str, Any]
    action: str
    existing_id: int | None = None


@dataclass(frozen=True)
class ReplacementPlan:
    story: dict[str, Any]
    delete_tasks: list[dict[str, Any]]
    create_tasks: list[CreatePlanItem]
    workflow_template: dict[str, Any]
    developer: dict[str, Any]
    tester: dict[str, Any]


class ManagedDevflowClient(DevflowClient):
    def get_task(self, task_id: int) -> dict[str, Any]:
        return self.request("GET", "/devflow/task/get", params={"id": task_id})

    def update_task(self, payload: dict[str, Any]) -> Any:
        return self.request("PUT", "/devflow/task/update", data=payload)

    def delete_task(self, task_id: int) -> Any:
        return self.request("DELETE", "/devflow/task/delete", params={"id": task_id})

    def disable_workflow(self, task_id: int) -> Any:
        return self.request("POST", "/devflow/task/disable-workflow", data={"taskId": task_id})

    def get_workflow_detail(self, task_id: int) -> dict[str, Any]:
        return self.request("GET", "/devflow/task/workflow-detail", params={"taskId": task_id})


def parse_plain_text_tasks(text: str) -> list[TaskInput]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text.strip()) if block.strip()]
    tasks: list[TaskInput] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        tasks.append(TaskInput(title=lines[0], body="\n".join(lines[1:]).strip()))
    if not tasks:
        raise DevflowError("No task blocks found in plain text input")
    return tasks


def parse_project_sprint_from_url(url: str | None) -> tuple[int | None, int | None]:
    if not url:
        return None, None
    query = parse_qs(urlparse(url).query)
    project_id = _first_int(query.get("projectId"))
    sprint_id = _first_int(query.get("sprintId"))
    return project_id, sprint_id


def match_req_tasks(
    tasks: list[dict[str, Any]],
    *,
    story_id: int,
    first: int,
    last: int,
) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    for task in tasks:
        if int(task.get("storyId") or 0) != story_id:
            continue
        title = str(task.get("title") or "")
        match = re.match(r"^\s*REQ[-_\s]?(\d+)\b", title, re.I)
        if not match:
            continue
        number = int(match.group(1))
        if first <= number <= last:
            matched.append(task)
    return sorted(matched, key=lambda task: int(task.get("id") or 0))


def build_replacement_plan(
    *,
    client: Any,
    project_id: int,
    sprint_id: int,
    story_id: int,
    story_title: str | None,
    delete_first: int,
    delete_last: int,
    task_specs: list[TaskInput],
    workflow_template_name: str,
    developer_nickname: str,
    tester_nickname: str,
    start_time: str,
    due_time: str,
) -> ReplacementPlan:
    stories = client.get_story_page(project_id, sprint_id)
    story = _find_story(stories, story_id=story_id, story_title=story_title)
    workflow_template = client.get_workflow_template(project_id, workflow_template_name)
    users = client.get_users()
    developer = _find_user(users, developer_nickname)
    tester = _find_user(users, tester_nickname)
    tasks = client.get_task_page(project_id, sprint_id)
    delete_tasks = match_req_tasks(
        tasks,
        story_id=int(story["id"]),
        first=delete_first,
        last=delete_last,
    )

    existing_by_title = {
        normalize_title(task.get("title") or ""): task
        for task in tasks
        if int(task.get("storyId") or 0) == int(story["id"])
    }
    surviving_tasks = [
        task
        for task in tasks
        if int(task.get("storyId") or 0) == int(story["id"])
        and int(task.get("id") or 0) not in {int(item["id"]) for item in delete_tasks}
    ]
    order_index = next_order_index(surviving_tasks)
    create_items: list[CreatePlanItem] = []
    for spec in task_specs:
        existing = existing_by_title.get(normalize_title(spec.title))
        payload = {
            "projectId": project_id,
            "sprintId": sprint_id,
            "storyId": int(story["id"]),
            "title": spec.title,
            "contentText": _task_markdown(spec),
            "type": DEFAULT_TASK_TYPE,
            "status": DEFAULT_TASK_STATUS,
            "priority": DEFAULT_PRIORITY,
            "orderIndex": order_index,
            "assigneeUserId": int(developer["id"]),
            "workflowTemplateId": int(workflow_template["id"]),
            "startTime": start_time,
            "dueTime": due_time,
        }
        workflow_payload = {
            "workflowAction": "NONE",
            "nodeUpdates": _build_two_node_workflow_updates(
                workflow_template,
                developer_id=int(developer["id"]),
                tester_id=int(tester["id"]),
            ),
        }
        create_items.append(
            CreatePlanItem(
                spec=spec,
                payload=payload,
                workflow_payload=workflow_payload,
                action="skip-existing" if existing else "create",
                existing_id=int(existing["id"]) if existing else None,
            )
        )
        order_index += 1000

    return ReplacementPlan(
        story=story,
        delete_tasks=delete_tasks,
        create_tasks=create_items,
        workflow_template=workflow_template,
        developer=developer,
        tester=tester,
    )


def execute_replacement_plan(
    *,
    client: ManagedDevflowClient,
    plan: ReplacementPlan,
    expected_delete_count: int | None,
    delay: float,
) -> dict[str, Any]:
    if expected_delete_count is not None and len(plan.delete_tasks) != expected_delete_count:
        raise DevflowError(
            f"Expected {expected_delete_count} tasks to delete, found {len(plan.delete_tasks)}"
        )

    deleted_ids: list[int] = []
    created_ids: list[int] = []
    skipped_existing_ids: list[int] = []
    for task in plan.delete_tasks:
        task_id = int(task["id"])
        client.delete_task(task_id)
        deleted_ids.append(task_id)
        time.sleep(delay)

    for item in plan.create_tasks:
        if item.existing_id:
            skipped_existing_ids.append(item.existing_id)
            continue
        task_id = int(client.create_task(item.payload))
        workflow_payload = {"taskId": task_id, **item.workflow_payload}
        if workflow_payload["nodeUpdates"]:
            client.update_workflow(workflow_payload)
        created_ids.append(task_id)
        time.sleep(delay)

    return {
        "deletedTaskIds": deleted_ids,
        "createdTaskIds": created_ids,
        "skippedExistingTaskIds": skipped_existing_ids,
    }


def verify_replacement(
    *,
    client: ManagedDevflowClient,
    project_id: int,
    sprint_id: int,
    story_id: int,
    delete_first: int,
    delete_last: int,
    expected_titles: list[str],
    workflow_template_id: int,
    developer_id: int,
    tester_id: int,
) -> dict[str, Any]:
    tasks = client.get_task_page(project_id, sprint_id)
    remaining_req = match_req_tasks(tasks, story_id=story_id, first=delete_first, last=delete_last)
    tasks_by_title = {
        normalize_title(task.get("title") or ""): task
        for task in tasks
        if int(task.get("storyId") or 0) == story_id
    }
    missing_titles = [
        title for title in expected_titles if normalize_title(title) not in tasks_by_title
    ]
    workflow_bad: list[dict[str, Any]] = []
    matched_task_ids: list[int] = []
    for title in expected_titles:
        task = tasks_by_title.get(normalize_title(title))
        if not task:
            continue
        task_id = int(task["id"])
        matched_task_ids.append(task_id)
        if (
            not task.get("workflowEnabled")
            or int(task.get("workflowTemplateId") or 0) != workflow_template_id
        ):
            workflow_bad.append(
                {
                    "id": task_id,
                    "title": title,
                    "reason": "workflow flag/template mismatch",
                    "workflowEnabled": task.get("workflowEnabled"),
                    "workflowTemplateId": task.get("workflowTemplateId"),
                }
            )
            continue
        try:
            detail = client.get_workflow_detail(task_id)
        except DevflowError as exc:
            workflow_bad.append({"id": task_id, "title": title, "reason": str(exc)})
            continue
        node_errors = _workflow_detail_errors(
            detail,
            developer_id=developer_id,
            tester_id=tester_id,
        )
        if node_errors:
            workflow_bad.append({"id": task_id, "title": title, "reason": node_errors})

    return {
        "remainingReqTasks": [
            {"id": task.get("id"), "title": task.get("title")} for task in remaining_req
        ],
        "matchedTaskIds": matched_task_ids,
        "missingTitles": missing_titles,
        "workflowBad": workflow_bad,
        "ok": not remaining_req and not missing_titles and not workflow_bad,
    }


def run(args: argparse.Namespace) -> int:
    project_from_url, sprint_from_url = parse_project_sprint_from_url(args.url)
    project_id = args.project_id or project_from_url
    sprint_id = args.sprint_id or sprint_from_url
    if not project_id or not sprint_id:
        raise DevflowError("projectId and sprintId are required, either by --url or flags")
    task_specs = parse_plain_text_tasks(Path(args.tasks_file).read_text(encoding="utf-8"))

    token = args.token or os.environ.get("DEVFLOW_TOKEN") or extract_chrome_token()
    if not token:
        raise DevflowError("No token found. Set DEVFLOW_TOKEN or log in to zxqijing.com in Chrome.")
    client = ManagedDevflowClient(token=token, base_url=args.base_url, tenant_id=args.tenant_id)

    plan = build_replacement_plan(
        client=client,
        project_id=project_id,
        sprint_id=sprint_id,
        story_id=args.story_id,
        story_title=args.story_title,
        delete_first=args.delete_first,
        delete_last=args.delete_last,
        task_specs=task_specs,
        workflow_template_name=args.workflow_template,
        developer_nickname=args.developer,
        tester_nickname=args.tester,
        start_time=args.start_time,
        due_time=args.due_time,
    )
    if args.expect_delete_count is not None and len(plan.delete_tasks) != args.expect_delete_count:
        raise DevflowError(
            f"Expected {args.expect_delete_count} tasks to delete, found {len(plan.delete_tasks)}"
        )

    log: dict[str, Any] = {
        "startedAt": dt.datetime.now().isoformat(),
        "execute": args.execute,
        "projectId": project_id,
        "sprintId": sprint_id,
        "story": {"id": plan.story.get("id"), "title": plan.story.get("title")},
        "deleteRange": {"first": args.delete_first, "last": args.delete_last},
        "deleteTasks": [
            {"id": task.get("id"), "title": task.get("title")} for task in plan.delete_tasks
        ],
        "createTasks": [
            {
                "title": item.spec.title,
                "action": item.action,
                "existingId": item.existing_id,
                "payload": item.payload,
                "workflowPayloadPreview": item.workflow_payload,
            }
            for item in plan.create_tasks
        ],
        "workflowTemplate": {
            "id": plan.workflow_template.get("id"),
            "name": plan.workflow_template.get("name"),
        },
        "assignees": {
            "developer": {"id": plan.developer.get("id"), "nickname": plan.developer.get("nickname")},
            "tester": {"id": plan.tester.get("id"), "nickname": plan.tester.get("nickname")},
        },
    }
    if args.execute:
        log["execution"] = execute_replacement_plan(
            client=client,
            plan=plan,
            expected_delete_count=args.expect_delete_count,
            delay=args.delay,
        )
        log["verification"] = verify_replacement(
            client=client,
            project_id=project_id,
            sprint_id=sprint_id,
            story_id=args.story_id,
            delete_first=args.delete_first,
            delete_last=args.delete_last,
            expected_titles=[task.title for task in task_specs],
            workflow_template_id=int(plan.workflow_template["id"]),
            developer_id=int(plan.developer["id"]),
            tester_id=int(plan.tester["id"]),
        )

    log_path = _write_log(log, Path(args.log_dir), "execute" if args.execute else "dry-run")
    summary = {
        "log": str(log_path),
        "execute": args.execute,
        "plannedDeletes": len(plan.delete_tasks),
        "plannedCreates": sum(1 for item in plan.create_tasks if item.action == "create"),
        "plannedSkippedExisting": sum(
            1 for item in plan.create_tasks if item.action == "skip-existing"
        ),
    }
    if args.execute:
        summary["execution"] = log["execution"]
        summary["verification"] = log["verification"]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not args.execute or log["verification"]["ok"] else 2


def _first_int(values: list[str] | None) -> int | None:
    if not values:
        return None
    try:
        return int(values[0])
    except (TypeError, ValueError):
        return None


def _find_story(
    stories: list[dict[str, Any]],
    *,
    story_id: int,
    story_title: str | None,
) -> dict[str, Any]:
    for story in stories:
        if int(story.get("id") or 0) == story_id:
            if story_title and story_title not in str(story.get("title") or ""):
                raise DevflowError(
                    f"Story id {story_id} title mismatch: {story.get('title')!r}"
                )
            return story
    raise DevflowError(f"Story id {story_id} was not found")


def _find_user(users: list[dict[str, Any]], nickname: str) -> dict[str, Any]:
    for user in users:
        if user.get("nickname") == nickname:
            return user
    raise DevflowError(f"User {nickname!r} was not found")


def _task_markdown(task: TaskInput) -> str:
    return f"### {task.title}\n\n{task.body}".strip()


def _build_two_node_workflow_updates(
    workflow_template: dict[str, Any],
    *,
    developer_id: int,
    tester_id: int,
) -> list[dict[str, Any]]:
    nodes = sorted(workflow_template.get("nodes") or [], key=lambda node: node.get("seqNo") or 0)
    updates: list[dict[str, Any]] = []
    for node in nodes:
        node_name = str(node.get("nodeName") or "")
        template_node_id = node.get("id")
        if node_name == "开发":
            updates.append(
                {
                    "templateNodeId": template_node_id,
                    "assigneeUserId": developer_id,
                    "bizStatus": 1,
                }
            )
        elif node_name == "测试":
            updates.append({"templateNodeId": template_node_id, "assigneeUserId": tester_id})
    if not updates:
        raise DevflowError("Workflow template has no 开发/测试 nodes")
    return updates


def _workflow_detail_errors(
    detail: dict[str, Any],
    *,
    developer_id: int,
    tester_id: int,
) -> list[str]:
    nodes = detail.get("nodes") or []
    by_name = {node.get("nodeName"): node for node in nodes}
    errors: list[str] = []
    developer_node = by_name.get("开发")
    tester_node = by_name.get("测试")
    if not developer_node or int(developer_node.get("assigneeUserId") or 0) != developer_id:
        errors.append("开发 node assignee mismatch")
    if not tester_node or int(tester_node.get("assigneeUserId") or 0) != tester_id:
        errors.append("测试 node assignee mismatch")
    return errors


def _write_log(log: dict[str, Any], log_dir: Path, mode: str) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"devflow-manage-{now_slug()}-{mode}.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    return log_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Devflow project URL containing projectId and sprintId")
    parser.add_argument("--project-id", type=int)
    parser.add_argument("--sprint-id", type=int)
    parser.add_argument("--story-id", type=int, required=True)
    parser.add_argument("--story-title")
    parser.add_argument("--tasks-file", required=True)
    parser.add_argument("--delete-first", type=int, default=1)
    parser.add_argument("--delete-last", type=int, default=13)
    parser.add_argument("--expect-delete-count", type=int)
    parser.add_argument("--developer", default="陈一安")
    parser.add_argument("--tester", default="颜沛杰")
    parser.add_argument("--start-time", default="2026-05-07 00:00:00")
    parser.add_argument("--due-time", default="2026-05-11 23:59:59")
    parser.add_argument("--workflow-template", default=DEFAULT_WORKFLOW_TEMPLATE_NAME)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--token")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--tenant-id", default=DEFAULT_TENANT_ID)
    parser.add_argument("--log-dir", default="docs/superpowers/logs")
    parser.add_argument("--delay", type=float, default=0.08)
    args = parser.parse_args()
    try:
        return run(args)
    except DevflowError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
