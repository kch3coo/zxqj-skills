---
name: yudao-start
description: Use when starting, restarting, or resetting local Yudao / ruoyi-vue-pro style full-stack projects such as Effy, CheckNM, Ruoqi, or Shanghai Yian, especially when frontend/backend ports conflict, Vite must point to the selected Spring Boot port, or Docker Compose MySQL volumes need to be recreated so init SQL runs again.
---

# Yudao Local Start Guide

这个 skill 负责本地开发环境启动，不负责业务代码分析。

当用户要启动 / 重启 Effy、CheckNM、Ruoqi、Shanghai Yian 这类 Yudao / 若依风格项目，或者要重置本地 MySQL volume 重新跑初始化 SQL，优先使用本 skill 自带脚本：

```bash
scripts/dev-start.sh
```

执行时将路径解析为当前 skill 目录下的 `scripts/dev-start.sh`。脚本默认项目根目录是 `$HOME/code`，如果项目不在这里，用 `CODE_ROOT=/path/to/code` 覆盖。

## 用户话术路由

用户可能会直接说 `yudao-start 帮我启动项目` 或 `yudao-start 帮我完整启动项目`。按下面的语义执行：

| 用户话术 | 含义 | 默认动作 |
| --- | --- | --- |
| `启动项目` / `帮我启动项目` | 启动后端和前端，不重置数据库 | `scripts/dev-start.sh <project>` |
| `完整启动项目` / `完整重启项目` | 先重置该项目 MySQL volume，让初始化 SQL 重新执行，再启动后端和前端 | 先 `scripts/dev-start.sh <project> --reset-db --yes`，再 `scripts/dev-start.sh <project>` |
| `启动数据库` / `启动依赖` | 只启动 Docker 依赖 | `scripts/dev-start.sh <project> --db-up` |
| `重置数据库` / `重新跑 SQL` / `删除 volume` | 重置 MySQL volume 并启动数据库依赖 | `scripts/dev-start.sh <project> --reset-db --yes` |

如果用户只说“启动项目”，不要自动重置数据库。

如果用户的表述不确定，例如“重新启动一下，可能 SQL 也要重跑”，先问一句：

```text
你要完整启动吗？完整启动会删除该项目本地 MySQL volume 并重新跑初始化 SQL；普通启动只启动后端和前端。
```

如果用户已经明确说“完整启动项目”，这就视为对重置本地 MySQL volume 的授权，不需要再次确认。

## 支持的项目别名

| 项目 | 命令别名 | 项目路径 |
| --- | --- | --- |
| Effy | `effy` | `$CODE_ROOT/Effy` |
| CheckNM | `checknm` | `$CODE_ROOT/checknm-system` |
| Ruoqi | `ruoqi` | `$CODE_ROOT/ruoqi-system` |
| Shanghai Yian | `yian` | `$CODE_ROOT/shanghai-yian-system` |

## 常用命令

启动某个项目的前端和后端：

```bash
scripts/dev-start.sh effy
scripts/dev-start.sh checknm
scripts/dev-start.sh ruoqi
scripts/dev-start.sh yian
```

只启动后端：

```bash
scripts/dev-start.sh effy --backend
```

只启动前端，并指定它连接哪个后端端口：

```bash
scripts/dev-start.sh effy --frontend --backend-port 48081
```

只启动数据库依赖：

```bash
scripts/dev-start.sh effy --db-up
```

重置该项目 MySQL volume 并重新启动数据库依赖：

```bash
scripts/dev-start.sh effy --reset-db --yes
```

完整启动项目，即先重置数据库，再启动后端和前端：

```bash
scripts/dev-start.sh effy --reset-db --yes
scripts/dev-start.sh effy
```

## 端口策略

脚本默认从这些端口开始找空闲端口：

- 前端：`3000`，冲突时递增到 `3001`、`3002`
- 后端：`48080`，冲突时递增到 `48081`、`48082`

脚本会临时注入：

```bash
VITE_BASE_URL=http://localhost:<本次后端端口>
```

这样前端端口和后端端口会成对匹配，避免前端启动成功但请求打到另一个项目。

可以用参数指定起始端口：

```bash
scripts/dev-start.sh yian --frontend-port 3010 --backend-port 48090
```

也可以用环境变量指定默认起点：

```bash
FRONTEND_BASE_PORT=3010 BACKEND_BASE_PORT=48090 scripts/dev-start.sh yian
```

## 数据库重置安全边界

`--reset-db` 是破坏性操作，会删除该项目的本地 MySQL Docker volume，让 `/docker-entrypoint-initdb.d` 下的初始化 SQL 在新 volume 上重新执行。

默认只删除 MySQL volume，不删除 Redis、EMQX 或其它 volume。

不要在用户只是说“启动项目”时自动重置数据库。只有当用户明确说“完整启动项目”、重置数据库、删除 volume、重新初始化、重新跑 SQL，或数据库状态明显需要重建且用户同意时，才使用：

```bash
scripts/dev-start.sh <project> --reset-db --yes
```

如果不确定，先 dry-run：

```bash
scripts/dev-start.sh <project> --reset-db --dry-run
```

## 重要限制

这些项目的 Docker Compose 数据库端口通常仍固定为：

- MySQL: `3306`
- Redis: `6379`
- Adminer: `38384`

所以当前脚本支持多个前后端自动错开端口，但数据库依赖更适合按项目切换启动。不要声称四套数据库可以无冲突同时运行，除非后续同时改造 Compose 端口和后端 datasource URL。

## 启动前检查

如果启动失败，优先检查：

```bash
scripts/dev-start.sh --help
lsof -nP -iTCP -sTCP:LISTEN
docker compose -f <backend>/script/docker/docker-compose.yml ps -a
docker compose -f <backend>/script/docker/docker-compose.yml config --volumes
```

不要先杀进程。先确认占用端口的进程路径和容器所属项目。

## 汇报方式

完成时说明：

- 使用了哪个项目别名
- 前端端口和后端端口
- 是否启动 / 重置了数据库
- 如果重置了数据库，删除的是哪个 MySQL volume
- 做过哪些验证，例如 `--dry-run`、`bash -n`、`docker compose ps`、端口监听检查
