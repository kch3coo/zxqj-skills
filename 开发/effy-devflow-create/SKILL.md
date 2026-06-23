---
name: effy-devflow-create
description: Use when creating Effy Devflow Story and Task records from a Markdown requirements document, especially docs with Story/Task headings, sprint/project ids, workflow templates, or requests to enable task workflows.
---

# Effy Devflow Create

## Overview

Create and manage Effy Devflow stories and tasks from Markdown, plain text, or OCR-confirmed image text. The bundled tools are deliberately conservative: dry-run by default, narrow title/story matching, JSON logs, and explicit workflow verification.

For user-specific nickname, person, and business shorthand mappings, read `references/project-mappings.md` before matching Effy users, stories, or tasks.

## Required Workflow: Markdown Story/Task Import

1. Locate the Markdown requirements document. Expected headings are `## Story N：标题` and nested `### Task N.N：标题`; schedule tables like `| Story | Task | 预计时间 | 开发者 |` are used to infer task assignees.
2. Run a dry-run first. Do not write to Devflow yet.
3. Run a single-item trial with `--execute --max-stories 1 --max-tasks 1`.
4. Verify the trial item exists and workflow is enabled.
5. Run the full `--execute` import. Existing stories/tasks with the same title are skipped.
6. Run `--verify-only` and report the created/skipped counts plus the log path.

Never print, paste, or write access tokens into logs. Prefer `DEVFLOW_TOKEN`; if absent, the script may read the local Chrome login token for `zxqijing.com`.

## Required Workflow: Existing Story Task Management

Use `scripts/devflow_manage_tasks.py` when the user wants to add tasks to an existing Story, replace old tasks, delete tasks, or update existing Effy tasks.

1. Identify the project/sprint/story from the page URL or explicit IDs.
2. For plain text, parse each blank-line-separated block as one task: first line is the task title, remaining lines are the task description.
3. For image input, extract/OCR text first and confirm the parsed task titles/descriptions before writing to Effy.
4. Run a dry-run first. Confirm the Story, delete matches, create payloads, workflow node assignees, and log path.
5. Use `--execute` only after the dry-run matches the user's requested scope.
6. Verify after execution: old tasks absent, new tasks present, workflow enabled, and expected workflow node assignees are set.

For destructive operations, always match by `storyId` plus an explicit title pattern/range. Do not delete similarly named tasks from other stories.

## Commands

Use the script by absolute path:

```bash
python3 /Users/annyye/.codex/skills/effy-devflow-create/scripts/devflow_import_stories.py \
  --spec docs/superpowers/specs/2026-05-07-membership-prepaid-card-next-stories.md \
  --project-id 3 \
  --sprint-id 8
```

Single-item trial:

```bash
python3 /Users/annyye/.codex/skills/effy-devflow-create/scripts/devflow_import_stories.py \
  --spec docs/superpowers/specs/2026-05-07-membership-prepaid-card-next-stories.md \
  --project-id 3 \
  --sprint-id 8 \
  --execute \
  --max-stories 1 \
  --max-tasks 1
```

Full import:

```bash
python3 /Users/annyye/.codex/skills/effy-devflow-create/scripts/devflow_import_stories.py \
  --spec docs/superpowers/specs/2026-05-07-membership-prepaid-card-next-stories.md \
  --project-id 3 \
  --sprint-id 8 \
  --execute
```

Verify only:

```bash
python3 /Users/annyye/.codex/skills/effy-devflow-create/scripts/devflow_import_stories.py \
  --spec docs/superpowers/specs/2026-05-07-membership-prepaid-card-next-stories.md \
  --project-id 3 \
  --sprint-id 8 \
  --verify-only
```

Manage existing Story tasks from plain text:

```bash
python3 /Users/annyye/.codex/skills/effy-devflow-create/scripts/devflow_manage_tasks.py \
  --url 'https://zxqijing.com/admin/devflow/project?projectId=2&sprintId=7' \
  --story-id 112 \
  --story-title '销售&库存&每日生产计划联动' \
  --tasks-file /path/to/tasks.txt \
  --delete-first 1 \
  --delete-last 13 \
  --expect-delete-count 13 \
  --developer '陈一安' \
  --tester '颜沛杰' \
  --start-time '2026-05-07 00:00:00' \
  --due-time '2026-05-11 23:59:59'
```

Execute after reviewing the dry-run:

```bash
python3 /Users/annyye/.codex/skills/effy-devflow-create/scripts/devflow_manage_tasks.py \
  --url 'https://zxqijing.com/admin/devflow/project?projectId=2&sprintId=7' \
  --story-id 112 \
  --story-title '销售&库存&每日生产计划联动' \
  --tasks-file /path/to/tasks.txt \
  --delete-first 1 \
  --delete-last 13 \
  --expect-delete-count 13 \
  --developer '陈一安' \
  --tester '颜沛杰' \
  --start-time '2026-05-07 00:00:00' \
  --due-time '2026-05-11 23:59:59' \
  --execute
```

Supported Devflow task APIs:

- `GET /devflow/task/page`
- `GET /devflow/task/get?id=...`
- `POST /devflow/task/create`
- `PUT /devflow/task/update`
- `DELETE /devflow/task/delete?id=...`
- `POST /devflow/task/update-workflow`
- `POST /devflow/task/disable-workflow`
- `GET /devflow/task/workflow-detail`

## User-Specific Rules

- When creating deployment tasks, do not enable workflow. Create the task with the confirmed assignee only, then verify `workflowEnabled=false`. If an existing helper script creates a deployment task with workflow enabled, immediately call `POST /devflow/task/disable-workflow` for that task and verify it is disabled.

## Defaults

- Base URL: `https://zxqijing.com/admin-api`
- Tenant: `1`
- Project: `3`
- Sprint: `8`
- Workflow template: `软件开发流程`
- Default task assignee: `胡广豪`
- Story defaults: `type=1`, `module=1`, `status=1`, `priority=2`
- Task defaults: `type=1`, `status=1`, `priority=2`

Override defaults with script flags when the page or user specifies different values.
