# Effy Release Troubleshooting

## 1. DMS 无法执行 SQL

症状：

- DMS API 或页面提示缺少服务角色
- 已给当前用户 `DMSFullAccess`，但仍然无法上传或执行 SQL

判断：

- 问题不在 RAM 用户调用权限，而在 DMS 服务是否被主账号授权代操作实例

处理：

1. 确认是否缺少 `AliyunDMSDefaultRole`
2. 用主账号完成 DMS 默认角色授权
3. 再重试 DMS SQL 上传或执行

规则：

- `DMSFullAccess` 不是 `AliyunDMSDefaultRole` 的替代品

## 2. Jenkins 后端报 `i: parameter not set`

症状：

- 后端构建和上传看似正常
- 启动阶段失败
- 日志出现 `script.sh.copy: 12: i: parameter not set`

根因：

- 远端 `start.sh` 使用了 bash 语法
- Jenkins 模板却用 `sh -c './start.sh'` 启动

处理：

1. 检查 Jenkins 模板是否显式使用 `bash './start.sh'`
2. 检查 Jenkins 已生效 job 配置是否真的更新
3. 如 Jar 已上传，可直接在目标机器执行 `bash ./start.sh` 做手工切换
4. 再回头修模板和远端 Jenkins 仓库

规则：

- 只改 Git 仓库不够，要确认 Jenkins job 配置和工作区都同步

## 3. Jenkins 页面失败，但服务其实已经起来

症状：

- Jenkins job 标红
- 目标机器上已有新 Jar 进程
- 健康检查返回 `200`

判断：

- 这是“发布平台状态失败”或“发布脚本失败”，不是业务服务一定失败

处理：

1. 登录目标主机检查进程、PID 文件、启动时间
2. 校验健康检查和页面访问
3. 如果服务已正常切换，保留 Jenkins 失败记录，但不要误判为整次发布失败
4. 后续修复 Jenkins 模板或 job 配置

## 4. 远端 Jenkins 仓库与生效配置不一致

症状：

- 本地仓库已 push 新 commit
- Jenkins 生效 job 配置可能已修，或仍是旧值
- Jenkins ECS 工作区 `git rev-parse HEAD` 仍停在旧 commit

判断：

- 至少存在三层状态：
  - Git 仓库 commit
  - Jenkins 生效 job 配置
  - Jenkins ECS 工作区

处理：

1. 在 Jenkins ECS 上检查 `/root/workspace/Jenkins`
2. 检查 `config.xml` 或 seed/job DSL 产物是否已更新
3. 如果仓库只是手工 patch 过，要把仓库正式补到目标 commit
4. 重新触发相关 job，再验证日志路径和远端行为

规则：

- 不要把“页面已经跑对一次”当成“仓库已经对齐”

## 5. 前端是否需要像后端一样重启

结论：

- 不需要
- 这个 Jenkins 模板是静态资源上传和解压覆盖

处理：

1. 核对 `dist.zip` 是否上传成功
2. 核对目标目录是否已解压到 `/home/effy-ui/dist-prod`
3. 再看 Nginx/静态托管是否命中新资源

规则：

- 前端问题优先从资源替换、缓存、静态托管看，不要套后端 `start.sh` 思路

## 6. 推荐最小恢复顺序

如果一次发布出现多点异常，按这个顺序切：

1. 先判断数据库是否已经变更
2. 再判断后端是否已经切到新进程
3. 最后判断前端是否已替换新资源

不要把三层问题混在一个动作里回滚。
