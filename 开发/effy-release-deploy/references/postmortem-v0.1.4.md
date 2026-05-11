# Effy `v0.1.4` Postmortem

## Summary

这次 `v0.1.4` 发布最终完成了数据库升级、前端发布、后端切换和 Jenkins 模板修复，但过程里暴露出多个发布链路缺口：

- 备份责任不在 Jenkins，需要人工先做
- DMS 执行权限依赖服务角色，不是单纯用户权限
- Jenkins 的仓库、job 配置、运行工作区不是同一层
- 后端启动对 shell 类型敏感，`sh` 与 `bash` 差异会直接导致上线失败
- Jenkins 结果不能替代生产实例健康检查

## What Went Wrong

### 1. 备份责任边界不清

- 一开始不确定 Jenkins 是否会自动做备份
- 事实是 Jenkins 这条链路不会替你完成 ECS/RDS 生产备份
- 结果是备份确认步骤被放到了人工补做，而不是流程内显式关口

规则：

- 发布前必须明确记录“ECS 手动快照已完成、RDS 手动备份已完成”

### 2. DMS 权限模型容易误判

- 试图通过阿里云 API/DMS API 执行 SQL 时，遇到角色授权问题
- `DMSFullAccess` 看起来像“权限已经足够”，但实际缺的不是 RAM 用户调用权限
- 真正缺的是主账号对 DMS 服务角色 `AliyunDMSDefaultRole` 的授权

规则：

- 遇到 DMS 无法代操作实例时，优先检查服务角色授权，不要只补用户侧权限

### 3. Jenkins 失败并不等于服务失败

- 后端 Jenkins 曾在启动阶段报错
- 但后续核对发现新 Jar 已经在目标机器上运行，健康检查也正常
- 这说明“Jenkins job 失败”和“服务实际不可用”是两件事

规则：

- 发布完成判定必须同时包含 Jenkins 结果、远端进程、健康检查

### 4. 后端模板对 shell 差异不稳健

- Jenkins 模板里通过 `sh -c './start.sh'` 触发远端脚本
- `start.sh` 内部依赖 bash 语法，导致 `i: parameter not set`
- 修复方式是把模板改为显式 `nohup bash './start.sh'`

规则：

- 远端启动脚本如果使用 bash 特性，Jenkins 模板必须显式指定 `bash`

### 5. Jenkins 三层状态被混用

- 本地仓库已提交并 push 新模板
- 但 Jenkins 已创建 job 不会因为 Git push 自动刷新
- Jenkins ECS 工作区甚至可能仍停留在旧 commit，只是被手工 patch 过

规则：

- 每次发布平台修复后，要分别确认：
  - 仓库 commit 是否正确
  - Jenkins job 配置是否已刷新
  - Jenkins ECS 工作区是否已对齐

### 6. 手工兜底是必要能力，不是例外

- 在 Jar 已上传而平台链路未完全打通时，直接在 ECS 上执行 `start.sh` 可以完成最终切换
- 这类手工兜底不应被视为“偏离流程”，而应被纳入恢复策略

规则：

- 当部署链路问题和业务进程问题可分离时，先保证服务切换成功，再修平台

## Permanent Changes From This Incident

- Jenkins 模板改成了显式 `bash` 启动后端脚本
- 远端 Jenkins 仓库被补齐到指定 commit，以消除仓库与实际工作区漂移
- 发布总结被沉淀为这个 skill，后续应按固定检查清单执行

## Release Standard Going Forward

以后 Effy 生产发布至少满足以下标准：

1. 备份完成才允许进入 SQL 或应用发布
2. SQL 成功后再触发应用层
3. 后端成功以进程和健康检查为准
4. 前端成功以资源替换和页面可访问为准
5. 平台修复后，要同步修仓库、job 配置和运行工作区
