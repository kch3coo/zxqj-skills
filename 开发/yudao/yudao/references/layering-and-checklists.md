# Yudao 分层约定与联动检查

这份文档用于 Yudao / ruoyi-vue-pro 项目的代码分析、方案设计和业务修改。  
当任务涉及字段、状态、主子表、权限、字典、导出或前后端联动时读取。

## 分层约定

### Controller

- 负责接收参数、调用 Service、返回统一响应、挂权限、日志和导出注解。
- 不承载复杂业务逻辑。

### Service

- 承载业务校验、状态流转、事务边界、主子表同步、下游单据生成。
- “是否允许新增 / 修改 / 删除” 这类判断放在 Service。
- 关键状态锁定、是否已生成下游单据、是否允许继续编辑等逻辑以后端为准。

### Mapper / DAL

- 负责清晰的 CRUD、条件查询、分页查询和轻量级 join。
- 遇到状态更新、批量更新、自增自减、数量类扣减等写操作时，先查仓库已有写法和封装，再决定是否新增。

### DO / VO / Convert

- DO 对应表字段；临时字段要显式标 `exist = false`。
- `SaveReqVO / PageReqVO / RespVO` 各司其职。
- 对象转换优先 MapStruct。

### Frontend API / View

- `src/api` 只负责接口和类型。
- `src/views` 负责展示、交互、调用 API 和体验型校验。
- 关键业务限制不能只写在前端。

## 改字段检查

- SQL 建表或字段定义
- DO / RespVO / SaveReqVO / PageReqVO
- Convert / Mapper 查询列
- 前端 interface、表单校验、表格列、详情展示
- 导入 / 导出 / 筛选条件 / 字典映射

## 改状态检查

- 状态字段定义和默认值
- Service 状态流转校验
- 错误码和提示语义
- 前端按钮显隐、可编辑态、列表展示、详情展示
- 是否影响下游单据生成、撤回、删除、关闭、审批等动作

## 改主子表检查

- 主表是否允许独立更新
- 明细是增量修改还是整体替换
- 明细新增 / 修改 / 删除是否有状态限制
- 生成下游单据后是否锁定来源单据
- 删除主表时是否联动清理明细

## 改权限 / 字典 / 导出检查

- 权限：`@PreAuthorize`、菜单权限标识、前端按钮权限
- 字典：后端值来源、前端选项、展示映射、筛选条件
- 导出：导出 VO、字典 / 枚举显示、筛选条件、导出列标题

## 框架能力优先级

优先复用这些约定，而不是自己起一套：

- `@PreAuthorize`
- `@DataPermission`
- `@ApiAccessLog` / 日志注解
- `ReturnCodeConstants` / `ErrorCodeConstants`
- `ExcelUtils`
- 框架 MQ / job / websocket 组件
- 项目已有字典工具和状态映射
- Mapper 现有更新 DSL / BaseMapperX 封装

## SQL 与 Upgrade

- 改表结构前，先确认需求是“改主建表 SQL”还是“明确要求 upgrade”。
- 不要默认同时改主 SQL 和 upgrade。
- 主子表、导入导出、历史数据兼容这类需求要单独确认边界。
