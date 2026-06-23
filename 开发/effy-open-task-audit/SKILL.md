---
name: effy-open-task-audit
description: Use when the user asks to check unfinished Effy tasks, overdue tasks, open tasks, tasks not completed, or wants an HTML review page for 未开始/进行中 Effy Devflow tasks across projects, active iterations, stories, and owners.
---

# Effy Open Task Audit

## Purpose

Use this skill for requests like “看下什么任务没完成”, “检查未开始/进行中的任务”, “哪些任务时间过期了”, or “生成一个待办任务确认页”.

The default output is an HTML review page that the user can annotate in the browser. Do not silently update tasks that are not explicitly confirmed by the user.

## Core Rules

- Only include Effy Devflow tasks whose status is `未开始` or `进行中`.
- Prefer scanning all projects and active iterations. If active-iteration discovery fails, say so directly and use the project/sprint URL the user provided.
- Group the HTML by project -> iteration -> story. Stories and projects should be collapsible; include “展开全部 / 折叠全部”.
- Each task card must have a stable selector `article#E{task_id}` for browser comments.
- Show task id, title, status, priority, assignee, start time, due time, project, iteration, and story.
- Existing due time earlier than today is a proposed update, not an immediate write, unless the user has confirmed the batch. Label it: `如未额外批注，将自动将截止时间改到今天`.
- Tasks with due time today or later wait for user comments; do not change them unless annotated.
- Tasks with empty due time wait for user comments; do not change them unless annotated.
- When applying comments, update only tasks explicitly identified by id or selector. Unannotated tasks are not changed.
- Interpret short dates like `5.12` as the current year and set due time to `YYYY-05-12 23:59:59`.
- Never print or write access tokens to output/logs.

## Recommended Commands

Generate a review page for the current project/sprint URL:

```bash
python3 /Users/annyye/.codex/skills/effy-open-task-audit/scripts/effy_open_task_audit.py \
  --url 'https://zxqijing.com/admin/devflow/project?projectId=2&sprintId=7'
```

Generate a review page for all discoverable active project iterations:

```bash
python3 /Users/annyye/.codex/skills/effy-open-task-audit/scripts/effy_open_task_audit.py \
  --all-active
```

Apply user-confirmed due-date comments:

```bash
python3 /Users/annyye/.codex/skills/effy-open-task-audit/scripts/effy_open_task_audit.py \
  --url 'https://zxqijing.com/admin/devflow/project?projectId=2&sprintId=7' \
  --apply-due '731=5.12,732=5.12'
```

Apply overdue tasks only after the user confirms the proposed batch:

```bash
python3 /Users/annyye/.codex/skills/effy-open-task-audit/scripts/effy_open_task_audit.py \
  --url 'https://zxqijing.com/admin/devflow/project?projectId=2&sprintId=7' \
  --execute-overdue
```

## Output Locations

- HTML: `/Users/annyye/Desktop/项目排期中心/effy-open-tasks-review.html`
- Logs: `/Users/annyye/Desktop/项目排期中心/archive/effy-open-task-*.json`

## Login Handling

Use `DEVFLOW_TOKEN` if present. Otherwise read the local Chrome login token for `zxqijing.com`.

If login fails, stop and tell the user directly: “现在登录态读不到，需要你先打开/登录 Effy 后我再继续.” Do not spend multiple turns attempting unrelated browser automation.
