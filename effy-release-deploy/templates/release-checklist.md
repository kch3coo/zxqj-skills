# Effy Release Checklist

## Before Release

- [ ] 确认目标 tag
- [ ] 确认升级 SQL 路径
- [ ] 确认回滚 SQL 路径
- [ ] 确认 App ECS 实例
- [ ] 确认 Jenkins ECS 实例
- [ ] 确认 ECS 手动快照已完成
- [ ] 确认 RDS 手动备份已完成
- [ ] 确认 Jenkins 任务名和参数
- [ ] 确认数据库目标实例和库名

## Database Stage

- [ ] DMS 连接到正确实例和库
- [ ] 如遇权限问题，先检查 `AliyunDMSDefaultRole`
- [ ] 执行升级 SQL
- [ ] 记录执行结果
- [ ] 校验关键表/关键数据

## Application Stage

- [ ] 触发 `effy-backend-release`
- [ ] 核对 `effy-ssh-check` 结果
- [ ] 核对 `effy-backend-deploy` 结果
- [ ] 触发 `effy-frontend-deploy`
- [ ] 核对前端构建产物和远端替换结果

## Runtime Verification

- [ ] 目标机器已有新后端进程
- [ ] `effy-server.pid` 已更新
- [ ] `http://47.113.110.80:48080/actuator/health/` 返回 `200`
- [ ] `https://47.113.110.80/` 返回 `200`
- [ ] 至少一个关键业务页面可访问

## Recovery Checks

- [ ] 若 SQL 失败，停止应用发布并保留日志
- [ ] 若后端失败，先看远端进程和健康检查
- [ ] 若前端失败，不要误动数据库
- [ ] 若 Jenkins 模板已修，确认仓库、job 配置、工作区三层都已同步
