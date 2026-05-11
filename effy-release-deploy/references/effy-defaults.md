# Effy Release Defaults

这份文件记录当前 Effy 生产发布默认环境，供 skill 作为示例和默认值引用。

## Core Targets

- App ECS: `i-wz9a0vh75xq4ai5qccyh`
- Jenkins ECS: `i-wz928up164hvnvclx17j`
- Region: `cn-shenzhen`
- Jenkins URL: `http://8.135.63.28:18080/`
- App Host: `47.113.110.80`

## Jenkins Jobs

- `effy-backend-release`
  - 上层发布入口
  - 传入 `TAG_NAME=vX.Y.Z`
  - 会串起 `effy-ssh-check` 和 `effy-backend-deploy`
- `effy-backend-deploy`
  - 负责后端构建、上传、远端启动
- `effy-frontend-deploy`
  - 负责前端静态资源构建、上传、解压覆盖
- `effy-ssh-check`
  - 负责发布前 SSH 可达性验证

## Remote Paths

- Backend Dir: `/home/effy-system`
- Backend Jar: `/home/effy-system/effy-server.jar`
- Backend Start Script: `/home/effy-system/start.sh`
- Backend Boot Log: `/home/effy-system/jenkins-start.log`
- Backend PID File: `/home/effy-system/effy-server.pid`
- Frontend Dir: `/home/effy-ui/dist-prod`

## Database Defaults

- RDS Endpoint: `rm-wz9qry648743d960c.mysql.rds.aliyuncs.com:3306`
- Database: `effy-sys-db`
- DMS is the preferred execution path for production SQL change.

## Current Known Good Checks

- Backend health: `http://47.113.110.80:48080/actuator/health/`
- Frontend homepage: `https://47.113.110.80/`

## Release Inputs From v0.1.4

- Tag: `v0.1.4`
- Upgrade SQL:
  - `/Users/kch3coo/code/Effy/effy-system-backend/sql/mysql/version-upgrade/upgrade20260419.sql`
- Rollback SQL:
  - `/Users/kch3coo/code/Effy/effy-system-backend/sql/mysql/version-upgrade/rollback20260419.sql`

## Operational Constraints

- Jenkins 不会替你做 ECS/RDS 备份，必须在阿里云侧单独确认。
- DMS SQL 变更依赖服务角色授权；只给当前 RAM 用户补 `DMSFullAccess` 不够。
- 前端发布是静态文件替换，不依赖 `start.sh`。
- 后端发布即使 Jenkins 页面失败，也要继续核对目标主机进程和健康检查。
