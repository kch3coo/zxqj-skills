---
name: effy-release-deploy
description: Use when deploying Effy to production through Aliyun backup, DMS SQL upgrade, Jenkins frontend/backend release, or when diagnosing Effy release failures such as DMS role issues, Jenkins config drift, backend start.sh shell mismatch, and remote repo mismatch.
---

# Effy Release Deploy

## Overview

Use this skill for Effy production releases that touch database upgrade, Jenkins deploy, and ECS runtime verification.

目标不是“把按钮点完”，而是让发布结果可验证、可恢复、可复盘。Jenkins 成功不等于发布成功；最终以数据库状态、目标机器进程和健康检查为准。

## When To Use

- 需要发布 Effy 新 tag 到生产
- 需要先做 ECS/RDS 备份，再执行 DMS SQL 升级和 Jenkins 发版
- 需要排查 Effy 发布异常，例如 DMS 授权、Jenkins 任务失败、后端未切换、新旧仓库漂移
- 需要把一次临时发布动作收敛成可重复执行的流程

不要用于：

- 普通本地开发构建
- 只改业务代码但不涉及生产发布
- 只生成数据库升级 SQL 的场景；那类问题优先用 `mysql-db-compare-upgrade`

## Default Release Order

1. 确认发布 tag、升级 SQL、回滚 SQL、目标实例。
2. 确认 ECS 和 RDS 手动备份已完成。
3. 通过 DMS 对生产库执行升级 SQL。
4. 触发 Jenkins 后端发布。
5. 触发 Jenkins 前端发布。
6. 在目标主机和外部入口做健康校验。
7. 如有失败，按数据库、后端、前端分层恢复，不要混在一起处理。

数据库升级默认先于应用发布，因为新后端可能依赖新表/新列。

## Success Criteria

- SQL 执行成功，且关键对象已存在或关键数据已写入
- Jenkins job 完成只是中间信号；最终必须再看：
  - 后端目标机器已有新进程
  - 健康检查返回 `200`
  - 前端页面可访问
- 如果 Jenkins 显示失败，但目标机器已切换到新进程且健康检查正常，应把问题归类为“发布平台失败”而不是“业务服务失败”

## Failure Rules

- 未确认 ECS/RDS 备份时，不进入发布阶段
- DMS 缺少服务角色授权时，不要把 `DMSFullAccess` 当成替代方案
- 后端 `start.sh` 使用 bash 语法时，Jenkins 模板必须显式用 `bash` 启动
- Jenkins 仓库提交更新后，必须区分：
  - Git 仓库 commit
  - Jenkins 已生效 job 配置
  - Jenkins ECS 上的实际工作区
- 如果远端 Jar 已上传但服务未切换，可以直接在 ECS 上手工执行 `start.sh` 完成切换，再回头修 Jenkins 模板或仓库

## Effy Defaults

- App ECS: `i-wz9a0vh75xq4ai5qccyh`
- Jenkins ECS: `i-wz928up164hvnvclx17j`
- Jenkins URL: `http://8.135.63.28:18080/`
- App Host: `47.113.110.80`
- Backend Dir: `/home/effy-system`
- Frontend Dir: `/home/effy-ui/dist-prod`
- Jenkins Jobs:
  - `effy-backend-release`
  - `effy-backend-deploy`
  - `effy-frontend-deploy`
  - `effy-ssh-check`

环境细节和已知故障模式见：

- [references/effy-defaults.md](references/effy-defaults.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [references/postmortem-v0.1.4.md](references/postmortem-v0.1.4.md)

## Quick Commands

本地核对入口只保留参数化形式，不假设你的仓库路径、系统或默认 shell：

```text
<health-check-url>
<jenkins-url>
<repo-check-command>
```

常用发布核对项：

```bash
curl -I http://47.113.110.80:48080/actuator/health/
curl -I https://47.113.110.80/
```

常用 Jenkins 仓库对齐核对：

```text
cd <jenkins-workspace>
git rev-parse HEAD
git status --short
```

使用阿里云 Cloud Assistant 在 Jenkins ECS 上核对工作区：

```bash
aliyun --mode AK --access-key-id "$ACCESS_KEY_ID" --access-key-secret "$ACCESS_KEY_SECRET" --region cn-shenzhen \
  ecs RunCommand \
  --RegionId cn-shenzhen \
  --Type RunShellScript \
  --CommandContent "cd <jenkins-workspace> && git rev-parse HEAD && git status --short" \
  --InstanceId.1 i-wz928up164hvnvclx17j
```

发布前后清单见 [templates/release-checklist.md](templates/release-checklist.md)。
