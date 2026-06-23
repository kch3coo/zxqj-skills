#!/usr/bin/env python3
"""Audit Effy Devflow open tasks and generate an annotation-friendly HTML review."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

BASE_URL = "https://zxqijing.com/admin-api"
TENANT_ID = "1"
OUT_DIR = Path("/Users/annyye/Desktop/项目排期中心")
ARCHIVE_DIR = OUT_DIR / "archive"
HTML_PATH = OUT_DIR / "effy-open-tasks-review.html"
OPEN_STATUSES = {1: "未开始", 2: "进行中"}
STATUS_CLASS = {1: "planned", 2: "active"}
STATUS_LABEL = {1: "未开始", 2: "进行中", 3: "已完成", 4: "已取消"}
PRIORITY_LABEL = {1: "低", 2: "中", 3: "高"}
LOCAL_TZ = dt.timezone(dt.timedelta(hours=8))


class DevflowError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Effy project URL with projectId and sprintId")
    parser.add_argument("--project-id", type=int)
    parser.add_argument("--sprint-id", type=int)
    parser.add_argument("--all-active", action="store_true", help="Try to scan all active iterations")
    parser.add_argument("--today", default=dt.datetime.now(LOCAL_TZ).date().isoformat())
    parser.add_argument("--output", default=str(HTML_PATH))
    parser.add_argument("--apply-due", help="Comma separated confirmed updates, e.g. 731=5.12,732=2026-05-12")
    parser.add_argument("--execute-overdue", action="store_true", help="Apply overdue proposals to today")
    return parser.parse_args()


def extract_project_sprint(url: str | None) -> tuple[int | None, int | None]:
    if not url:
        return None, None
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    project_id = _first_int(query.get("projectId"))
    sprint_id = _first_int(query.get("sprintId"))
    return project_id, sprint_id


def _first_int(values: list[str] | None) -> int | None:
    if not values:
        return None
    try:
        return int(values[0])
    except (TypeError, ValueError):
        return None


def chrome_token_candidates() -> list[str]:
    env_token = os.environ.get("DEVFLOW_TOKEN")
    if env_token:
        return [env_token]
    root = Path.home() / "Library/Application Support/Google/Chrome"
    files: list[Path] = []
    for profile in ("Default", "Profile 5", "Profile 1", "Profile 2", "Profile 3", "Profile 4"):
        leveldb = root / profile / "Local Storage/leveldb"
        if leveldb.exists():
            files.extend(leveldb.glob("*.ldb"))
            files.extend(leveldb.glob("*.log"))
    patterns = [
        re.compile(
            rb'ACCESS_TOKEN(?:S)?[^\{]{0,260}\{\"c\":(\d+),\"e\":\d+,\"v\":\"\\?\"([0-9a-f]{32})\\?\"\"\}',
            re.S,
        ),
        re.compile(rb"ACCESS_TOKEN.{0,1200}?([0-9a-f]{32})", re.S),
    ]
    seen: set[str] = set()
    tokens: list[str] = []
    for path in files:
        try:
            data = path.read_bytes()
        except OSError:
            continue
        for pattern in patterns:
            for match in pattern.finditer(data):
                token = match.group(match.lastindex).decode("ascii", "ignore")
                if token and token not in seen:
                    seen.add(token)
                    tokens.append(token)
    return tokens


class Client:
    def __init__(self, token: str):
        self.token = token

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, data: dict[str, Any] | None = None) -> Any:
        url = BASE_URL + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        body = None if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("tenant-id", TENANT_ID)
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            raise DevflowError(f"{method} {path} HTTP {exc.code}: {raw}") from exc
        code = payload.get("code")
        if code not in (0, "0", 200, "200"):
            raise DevflowError(f"{method} {path} returned code={code}: {payload.get('msg')}")
        return payload.get("data")

    def tasks(self, project_id: int, sprint_id: int) -> list[dict[str, Any]]:
        data = self.request("GET", "/devflow/task/page", params={"pageNo": 1, "pageSize": -1, "projectId": project_id, "sprintId": sprint_id})
        return data.get("list") or []

    def stories(self, project_id: int, sprint_id: int) -> list[dict[str, Any]]:
        data = self.request("GET", "/devflow/story/page", params={"pageNo": 1, "pageSize": -1, "projectId": project_id, "sprintId": sprint_id})
        return data.get("list") or []

    def task(self, task_id: int) -> dict[str, Any]:
        return self.request("GET", "/devflow/task/get", params={"id": task_id})

    def update_task(self, payload: dict[str, Any]) -> Any:
        return self.request("PUT", "/devflow/task/update", data=payload)

    def users(self) -> list[dict[str, Any]]:
        return self.request("GET", "/system/user/simple-list") or []


def get_client() -> Client:
    for token in chrome_token_candidates():
        client = Client(token)
        try:
            client.request("GET", "/system/user/simple-list")
            return client
        except Exception:
            continue
    raise DevflowError("LOGIN_FAILED")


def list_active_scopes(client: Client) -> list[dict[str, Any]]:
    """Best-effort discovery. Effy installs vary; caller falls back to explicit URL."""
    scopes: list[dict[str, Any]] = []
    project_data = try_page(client, "/devflow/project/page", {"pageNo": 1, "pageSize": -1})
    projects = project_data or []
    for project in projects:
        project_id = int(project.get("id") or 0)
        if not project_id:
            continue
        sprint_data = (
            try_page(client, "/devflow/sprint/page", {"pageNo": 1, "pageSize": -1, "projectId": project_id})
            or try_page(client, "/devflow/iteration/page", {"pageNo": 1, "pageSize": -1, "projectId": project_id})
        )
        for sprint in sprint_data or []:
            if not is_active_sprint(sprint):
                continue
            scopes.append({
                "projectId": project_id,
                "projectTitle": project.get("name") or project.get("title") or f"Project {project_id}",
                "sprintId": int(sprint.get("id")),
                "sprintTitle": sprint.get("name") or sprint.get("title") or f"Sprint {sprint.get('id')}",
            })
    return scopes


def try_page(client: Client, path: str, params: dict[str, Any]) -> list[dict[str, Any]] | None:
    try:
        data = client.request("GET", path, params=params)
    except Exception:
        return None
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("list") or data.get("records") or data.get("items")
    return None


def is_active_sprint(sprint: dict[str, Any]) -> bool:
    text = " ".join(str(sprint.get(key) or "") for key in ("status", "statusName", "name", "title"))
    if "已完成" in text or "归档" in text or "关闭" in text:
        return False
    numeric = sprint.get("status")
    return numeric in (None, 0, 1, 2, "0", "1", "2")


def resolve_scopes(args: argparse.Namespace, client: Client) -> list[dict[str, Any]]:
    if args.all_active:
        scopes = list_active_scopes(client)
        if scopes:
            return scopes
    url_project, url_sprint = extract_project_sprint(args.url)
    project_id = args.project_id or url_project
    sprint_id = args.sprint_id or url_sprint
    if not project_id or not sprint_id:
        raise DevflowError("Need --url with projectId/sprintId or --project-id and --sprint-id")
    return [{"projectId": project_id, "sprintId": sprint_id, "projectTitle": f"Project {project_id}", "sprintTitle": f"Sprint {sprint_id}"}]


def parse_date(value: str, today: dt.date) -> dt.date:
    value = value.strip()
    match = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})", value)
    if match:
        return dt.date(today.year, int(match.group(1)), int(match.group(2)))
    return dt.date.fromisoformat(value)


def parse_apply_due(value: str | None, today: dt.date) -> dict[int, str]:
    updates: dict[int, str] = {}
    if not value:
        return updates
    for item in value.split(","):
        if not item.strip():
            continue
        task_id, date_text = item.split("=", 1)
        due_date = parse_date(date_text, today)
        updates[int(task_id.strip().lstrip("#E"))] = f"{due_date.isoformat()} 23:59:59"
    return updates


def to_date(value: Any) -> dt.date | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value / 1000, LOCAL_TZ).date()
    text = str(value)
    try:
        return dt.date.fromisoformat(text[:10])
    except ValueError:
        return None


def fmt_dt(value: Any) -> str:
    if not value:
        return "未填"
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value / 1000, LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def fmt_date_range(task: dict[str, Any]) -> str:
    start = to_date(task.get("startTime"))
    due = to_date(task.get("dueTime"))
    if start and due:
        return start.isoformat() if start == due else f"{start.isoformat()} 至 {due.isoformat()}"
    if start:
        return start.isoformat()
    if due:
        return due.isoformat()
    return "未填"


def collect(client: Client, scopes: list[dict[str, Any]], today: dt.date, user_by_id: dict[int, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for scope in scopes:
        try:
            stories = client.stories(scope["projectId"], scope["sprintId"])
            tasks = client.tasks(scope["projectId"], scope["sprintId"])
        except Exception as exc:
            errors.append({**scope, "error": str(exc)})
            continue
        story_by_id = {int(story.get("id") or 0): story for story in stories}
        for task in tasks:
            status = int(task.get("status") or 0)
            if status not in OPEN_STATUSES:
                continue
            story = story_by_id.get(int(task.get("storyId") or 0), {})
            due_date = to_date(task.get("dueTime"))
            if not due_date:
                action = "empty"
            elif due_date < today:
                action = "overdue_proposed"
            else:
                action = "wait_comment"
            rows.append({
                "task": task,
                "scope": scope,
                "story": story,
                "status": status,
                "action": action,
                "dueDate": due_date.isoformat() if due_date else "",
                "ownerName": owner_name(task, user_by_id),
            })
    return rows, errors


def owner_name(task: dict[str, Any], user_by_id: dict[int, str]) -> str:
    direct = (
        task.get("assigneeUserNickname")
        or task.get("assigneeNickname")
        or task.get("assigneeUserName")
        or task.get("ownerName")
    )
    if direct:
        return str(direct)
    user_id = task.get("assigneeUserId")
    try:
        return user_by_id.get(int(user_id), "未分配")
    except (TypeError, ValueError):
        return "未分配"


def apply_updates(client: Client, updates: dict[int, str], reason: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for task_id, due_time in updates.items():
        task = client.task(task_id)
        old = task.get("dueTime")
        task["dueTime"] = due_time
        client.update_task(task)
        after = client.task(task_id)
        results.append({"id": task_id, "title": after.get("title"), "oldDueTime": old, "newDueTime": after.get("dueTime"), "reason": reason})
        time.sleep(0.1)
    return results


def write_html(rows: list[dict[str, Any]], errors: list[dict[str, Any]], today: dt.date, output: Path, log_name: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    generated_at = dt.datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    project_groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = f"{row['scope'].get('projectTitle')} / {row['scope'].get('sprintTitle')}"
        project_groups.setdefault(key, []).append(row)

    cards = []
    story_options: set[str] = set()
    for project_key, project_rows in project_groups.items():
        by_story: dict[str, list[dict[str, Any]]] = {}
        for row in project_rows:
            story_title = row["story"].get("title") or f"Story {row['task'].get('storyId')}"
            by_story.setdefault(story_title, []).append(row)
            story_options.add(story_title)
        story_html = []
        for story_title, story_rows in by_story.items():
            task_html = "\n".join(task_card(row, today) for row in story_rows)
            story_html.append(f"""
          <details class="story" open data-story="{esc(story_title)}">
            <summary><span>{esc(story_title)}</span><b>{len(story_rows)} tasks</b></summary>
            {task_html}
          </details>""")
        cards.append(f"""
      <details class="project" open>
        <summary><span>{esc(project_key)}</span><b>{len(project_rows)} tasks</b></summary>
        {''.join(story_html)}
      </details>""")

    story_select = "\n".join(f'<option value="{esc(story)}">{esc(story)}</option>' for story in sorted(story_options))
    error_html = "" if not errors else "<section class='panel warn'><h2>读取失败范围</h2><pre>" + esc(json.dumps(errors, ensure_ascii=False, indent=2)) + "</pre></section>"
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Effy 未完成任务巡检</title>
  <style>
    :root {{ --bg:#f7f3eb; --paper:#fffdf8; --ink:#22324a; --muted:#667085; --line:#dfd4c3; --active:#fff5d6; --planned:#eaf2ff; --warn:#fff3df; --ok:#edf8f1; --bad:#fff1f0; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:linear-gradient(90deg, rgba(118,95,63,.08) 1px, transparent 1px), linear-gradient(rgba(118,95,63,.08) 1px, transparent 1px), var(--bg); background-size:24px 24px; color:var(--ink); font:15px/1.55 -apple-system,BlinkMacSystemFont,\"Segoe UI\",sans-serif; }}
    header.top {{ position:sticky; top:0; z-index:5; background:rgba(247,243,235,.96); border-bottom:1px solid var(--line); padding:18px 22px 14px; backdrop-filter:blur(8px); }}
    h1 {{ margin:0; font-size:28px; letter-spacing:0; }}
    .sub {{ margin:5px 0 0; color:var(--muted); }}
    .toolbar {{ display:grid; grid-template-columns:1fr 150px 180px 120px 120px; gap:10px; margin-top:14px; }}
    input, select, button {{ height:42px; border:1px solid var(--line); border-radius:7px; background:var(--paper); color:var(--ink); padding:0 12px; font:inherit; }}
    button {{ cursor:pointer; }}
    main {{ max-width:1120px; margin:20px auto 60px; padding:0 18px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:14px; }}
    .metric,.panel,.project,.story,.task {{ background:var(--paper); border:1px solid var(--line); border-radius:8px; }}
    .metric {{ padding:14px; }} .metric b {{ display:block; font-size:24px; }}
    .note {{ border:1px solid #e5b65d; background:#fff8e8; border-radius:8px; padding:13px 16px; margin-bottom:16px; }}
    details.project {{ margin:14px 0 22px; overflow:hidden; }}
    details > summary {{ list-style:none; cursor:pointer; display:flex; justify-content:space-between; align-items:center; gap:12px; padding:16px 18px; background:#eee6d8; font-weight:700; font-size:20px; }}
    details.story {{ margin:0; border-width:1px 0 0; border-radius:0; }}
    details.story > summary {{ background:#f8f4ec; font-size:17px; padding-left:26px; }}
    .task {{ margin:0; border-width:1px 0 0; border-radius:0; padding:18px; }}
    .task.overdue_proposed {{ background:var(--bad); }}
    .task.empty {{ background:var(--warn); }}
    .task.wait_comment {{ background:var(--paper); }}
    .task-head {{ display:flex; align-items:flex-start; gap:14px; }}
    .badge-id {{ flex:0 0 auto; width:52px; height:52px; border:1px solid var(--line); border-radius:50%; display:grid; place-items:center; background:#fff; font-weight:700; }}
    h3 {{ margin:0 0 9px; font-size:19px; letter-spacing:0; }}
    .pills {{ display:flex; flex-wrap:wrap; gap:7px; }}
    .pill {{ border:1px solid var(--line); border-radius:999px; padding:3px 10px; background:#fff; color:var(--muted); }}
    .pill.active {{ background:#fff1c2; color:#a05a00; border-color:#e6bd69; }}
    .pill.planned {{ background:#e7f1ff; color:#2364b8; border-color:#acd0ff; }}
    .pill.action-overdue {{ background:#fff0ef; color:#c13d36; border-color:#f1aaa6; }}
    .pill.action-empty {{ background:#fff7e6; color:#b26b00; border-color:#e6bd69; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-top:13px; color:var(--muted); }}
    .grid b {{ display:block; color:var(--ink); margin-top:3px; overflow-wrap:anywhere; }}
    .action {{ margin:14px 0 0; border-left:3px solid #d9a441; padding-left:10px; color:#604816; }}
    .hide {{ display:none !important; }}
    pre {{ overflow:auto; white-space:pre-wrap; }}
    @media (max-width:760px) {{ .toolbar,.metrics,.grid {{ grid-template-columns:1fr; }} header.top {{ padding:16px 18px; }} }}
  </style>
</head>
<body>
  <header class="top">
    <h1>Effy 未完成任务巡检</h1>
    <p class="sub">生成时间 {esc(generated_at)} · 今天 {today.isoformat()} · 只展示未开始和进行中 · 日志 {esc(log_name)}</p>
    <div class="toolbar">
      <input id="q" placeholder="搜索任务编号、标题、负责人、Story">
      <select id="status"><option value="">全部状态</option><option>未开始</option><option>进行中</option></select>
      <select id="story"><option value="">全部 Story</option>{story_select}</select>
      <button id="expand">展开全部</button>
      <button id="collapse">折叠全部</button>
    </div>
  </header>
  <main>
    <section class="metrics">
      <div class="metric"><b>{len(rows)}</b><span>未完成任务</span></div>
      <div class="metric"><b>{sum(1 for r in rows if r['action']=='overdue_proposed')}</b><span>早于今天，待确认自动改</span></div>
      <div class="metric"><b>{sum(1 for r in rows if r['action']=='empty')}</b><span>截止时间为空</span></div>
      <div class="metric"><b>{len(project_groups)}</b><span>项目/迭代范围</span></div>
    </section>
    <div class="note">规则：早于今天的已有截止时间先显示为建议项；如果你确认批量更新，我才会改到今天。当天或之后的任务、空截止时间任务，都等你批注后再改。你没批注的内容不会修改。</div>
    {error_html}
    <div id="doc">{''.join(cards)}</div>
  </main>
  <script>
    const q = document.getElementById('q'), status = document.getElementById('status'), story = document.getElementById('story');
    function filter() {{
      const query = q.value.trim().toLowerCase();
      document.querySelectorAll('.task').forEach(card => {{
        const text = card.innerText.toLowerCase();
        const ok = (!query || text.includes(query)) && (!status.value || card.dataset.status === status.value) && (!story.value || card.dataset.story === story.value);
        card.classList.toggle('hide', !ok);
      }});
      document.querySelectorAll('details.story').forEach(d => {{
        const visible = [...d.querySelectorAll('.task')].some(t => !t.classList.contains('hide'));
        d.classList.toggle('hide', !visible);
      }});
      document.querySelectorAll('details.project').forEach(d => {{
        const visible = [...d.querySelectorAll('.story')].some(t => !t.classList.contains('hide'));
        d.classList.toggle('hide', !visible);
      }});
    }}
    [q,status,story].forEach(el => el.addEventListener('input', filter));
    document.getElementById('expand').onclick = () => document.querySelectorAll('details').forEach(d => d.open = true);
    document.getElementById('collapse').onclick = () => document.querySelectorAll('details').forEach(d => d.open = false);
  </script>
</body>
</html>"""
    output.write_text(html_text, encoding="utf-8")


def task_card(row: dict[str, Any], today: dt.date) -> str:
    task = row["task"]
    story = row["story"].get("title") or f"Story {task.get('storyId')}"
    status = row["status"]
    action = row["action"]
    due = to_date(task.get("dueTime"))
    if action == "overdue_proposed":
        action_text = f"如未额外批注，将自动将截止时间改到今天 {today.isoformat()}"
        action_class = "action-overdue"
    elif action == "empty":
        action_text = "截止时间为空，等待批注"
        action_class = "action-empty"
    else:
        action_text = "时间为当天或之后，等待批注"
        action_class = ""
    owner = row.get("ownerName") or owner_name(task, {})
    priority = PRIORITY_LABEL.get(int(task.get("priority") or 0), str(task.get("priority") or "未填"))
    return f"""
            <article id="E{int(task.get('id'))}" class="task {esc(action)}" data-status="{esc(OPEN_STATUSES[status])}" data-story="{esc(story)}" data-owner="{esc(owner)}">
              <div class="task-head">
                <div class="badge-id">#{int(task.get('id'))}</div>
                <div>
                  <h3>{esc(task.get('title') or '')}</h3>
                  <div class="pills">
                    <span class="pill {STATUS_CLASS[status]}">{esc(OPEN_STATUSES[status])}</span>
                    <span class="pill">优先级 {esc(priority)}</span>
                    <span class="pill">{esc(owner)}</span>
                    <span class="pill">{esc(fmt_date_range(task))}</span>
                    <span class="pill {action_class}">{esc(action_text)}</span>
                  </div>
                </div>
              </div>
              <div class="grid">
                <span>任务编号<b>#{int(task.get('id'))}</b></span>
                <span>状态<b>{esc(OPEN_STATUSES[status])}</b></span>
                <span>优先级<b>{esc(priority)}</b></span>
                <span>负责人<b>{esc(owner)}</b></span>
                <span>开始时间<b>{esc(fmt_dt(task.get('startTime')))}</b></span>
                <span>截止时间<b>{esc(fmt_dt(task.get('dueTime')))}</b></span>
                <span>Story<b>{esc(story)}</b></span>
                <span>动作<b>{esc(action_text)}</b></span>
              </div>
              <p class="action">{esc(action_text)}</p>
            </article>"""


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def write_log(name: str, payload: dict[str, Any]) -> Path:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    path = ARCHIVE_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    today = dt.date.fromisoformat(args.today)
    try:
        client = get_client()
    except DevflowError:
        print("LOGIN_FAILED: 现在登录态读不到，需要先打开/登录 Effy 后再继续。", file=sys.stderr)
        return 2

    scopes = resolve_scopes(args, client)
    users = client.users()
    user_by_id = {int(user["id"]): str(user.get("nickname") or user.get("name") or user["id"]) for user in users if user.get("id") is not None}
    confirmed_updates = parse_apply_due(args.apply_due, today)
    applied: list[dict[str, Any]] = []
    if confirmed_updates:
        applied.extend(apply_updates(client, confirmed_updates, "confirmed_comment"))

    rows, errors = collect(client, scopes, today, user_by_id)
    if args.execute_overdue:
        overdue_updates: dict[int, str] = {}
        for row in rows:
            if row["action"] == "overdue_proposed":
                overdue_updates[int(row["task"]["id"])] = f"{today.isoformat()} 23:59:59"
        applied.extend(apply_updates(client, overdue_updates, "confirmed_overdue_batch"))
        rows, errors = collect(client, scopes, today, user_by_id)

    timestamp = dt.datetime.now(LOCAL_TZ).strftime("%Y%m%d-%H%M%S")
    log_payload = {
        "createdAt": dt.datetime.now(LOCAL_TZ).isoformat(),
        "today": today.isoformat(),
        "scopes": scopes,
        "openTaskCount": len(rows),
        "overdueProposalCount": sum(1 for row in rows if row["action"] == "overdue_proposed"),
        "emptyDueTimeCount": sum(1 for row in rows if row["action"] == "empty"),
        "appliedUpdates": applied,
        "errors": errors,
    }
    log_path = write_log(f"effy-open-task-audit-{timestamp}.json", log_payload)
    write_html(rows, errors, today, Path(args.output), log_path.name)
    print(json.dumps({"ok": True, "html": str(args.output), "log": str(log_path), **{k: log_payload[k] for k in ("openTaskCount", "overdueProposalCount", "emptyDueTimeCount")}}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
