---
name: mysql-db-compare-upgrade
description: Use when a MySQL project needs a tool-generated upgrade script from db-compare, with project-specific source/target DB preparation and a final compare proving both sides are fully aligned.
---

# MySQL DB Compare Upgrade

## Overview

Use this skill to generate and verify an upgrade SQL with the repository's cross-platform Python runner.

真实性标准只有一个：`upgrade.sql` 执行后，再次 compare 必须无差异。不要手写升级 SQL，不要把结果当成“看起来合理”。

## When To Use

- 需要根据某个 compare 配置生成 MySQL 升级脚本
- 需要先准备 source/target 数据库，再做 compare 与 upgrade 验真
- 需要证明升级脚本执行后 source 与 target 完全一致

不要用于：

- 日常业务开发时修改模块 SQL 文件
- 手工维护项目里的 version-upgrade SQL
- 没有准备好 compare 配置或数据库准备方案时的猜测性升级

## Required Inputs

- 一个 YAML adapter 文件
- 一个 compare 配置 YAML
- 可被自动发现或显式传参的 `db-compare` 仓库
- `templates/project-template.yaml` 作为适配协议参考
- `templates/effy-template.yaml` 作为 Effy 示例

## Runtime Entry

统一入口：

```bash
python -m script.python.mysql_db_compare_upgrade run --adapter /path/to/project-adapter.yml
```

可选覆盖参数：

- `--project-root`
- `--db-compare-repo`
- `--compare-config`
- `--generated-dir`

路径解析顺序固定为：

1. CLI 显式参数
2. 从当前工作目录向上自动发现项目根
3. 按项目根解析 adapter 内相对路径
4. 自动发现 `db-compare` 仓库
5. 仍失败时，明确报出缺失路径并要求用户提供

## Adapter Contract

adapter 必填：

- `project_root_markers`
- `compare_config_file`
- `backup_tar`
- `generated_dir`
- `source_db`
- `target_db`

adapter 可选：

- `db_compare_repo_candidates`
- `runtime_compare`
- `sql_validation_rules`
- `prepare_steps`

所有相对路径都相对 `project_root` 解析，不相对 adapter 文件本身。

`source_db` / `target_db` 至少应提供：

- `host`
- `port`
- `username`
- `password`
- `database`
- `access`

`access.kind` 支持：

- `mysql_cli`
- `docker_exec`

## Workflow

1. 解析 adapter，自动发现项目根与 `db-compare` 仓库。
2. 生成运行时 compare 配置，并把 adapter 的 source/target DB 写入其中。
3. 执行 `prepare_steps.target` 与 `prepare_steps.source`。
4. 等待 source/target 数据库可登录。
5. 调 `db-compare` backend 做首次 compare。
6. 下载 upgrade SQL 与 rollback SQL。
7. 执行 SQL 校验规则。
8. 在运行时 `source_db` 上执行 upgrade SQL。
9. 再次 compare 验真。
10. 只有 post-compare 无差异时，才算成功。

## Outputs

输出目录由 `generated_dir` 决定：

- `<config-name>.runtime.yml`
- `<config-name>.upgrade.sql`
- `<config-name>.rollback.sql`
- `pre-compare.json`
- `post-compare.json`
- `residual-diff.json`，仅在二次 compare 仍有差异时生成
- `db-compare-backend.log`，仅在脚本代启后端时生成
- `db-compare-frontend.log`，仅在 `start` 子命令代启前端时生成

## Failure Rules

- adapter 缺失必填字段：立即失败
- 项目根无法自动发现：立即失败，并提示 `--project-root`
- `db-compare` 仓库无法自动发现：立即失败，并提示 `--db-compare-repo`
- 备份文件缺失：立即失败
- `db-compare` 后端不可用且无法自动启动：立即失败
- 首次 compare 无差异：直接报告已一致，不生成空 upgrade
- 首次 compare 有差异但下载到空 upgrade SQL：视为工具异常并失败
- 下载到空 rollback SQL：视为工具异常并失败
- SQL 校验失败：立即失败，不执行 upgrade
- upgrade SQL 执行失败：立即失败，不继续 recompare
- recompare 仍有差异：保存 `residual-diff.json` 并失败

## Important Rules

- 升级脚本是工具产物，不是日常模块 SQL 的替代物
- 默认不要手写升级 SQL
- 项目仓库里的额外 SQL 规则由 adapter 或项目文档约束
- “升级方向”必须先确认清楚：最终执行 upgrade 的总是运行时 `source_db`
- 如果表的业务唯一键不是自增主键，应通过 `runtime_compare.append_specified_primary_keys` 明确补充
- 如果生成 SQL 出现工具辅助列（例如 `__parent_*`），必须通过 `sql_validation_rules` 直接拦截

## Quick Commands

Effy 默认入口：

```bash
python -m script.python.mysql_db_compare_upgrade run --adapter script/db-compare/adapters/effy-adapter.yml
```

只想启动 `db-compare` 前后端并暴露 compare 配置时：

```bash
python -m script.python.mysql_db_compare_upgrade start --adapter script/db-compare/adapters/effy-adapter.yml
```

需要覆盖自动发现结果时：

```bash
python -m script.python.mysql_db_compare_upgrade run \
  --adapter script/db-compare/adapters/effy-adapter.yml \
  --project-root /path/to/project \
  --db-compare-repo /path/to/db-compare
```

API 细节见 [references/db-compare-api.md](references/db-compare-api.md)。
