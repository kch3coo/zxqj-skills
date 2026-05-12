---
name: yudao
description: Use when working on Yudao, 芋道, ruoyi-vue-pro, or 若依风格 projects, especially for 代码梳理, 写方案, 测试用例, Playwright 场景, API or SQL changes, form/field linkage, dictionary/error-code updates, main-detail flows, status transitions, frontend-backend debugging, database constraints, codegen, or tracing Controller/Service/Mapper/DO/VO/API/View chains.
---

# Yudao Common Execution Guide

这个 skill 是**所有 Yudao / ruoyi-vue-pro 项目的通用方法层**。  
它不绑定某个具体仓库，只提供跨项目都适用的分析路径、分层约定、联动检查项和方案输出方式。

全局底线仍以当前 Codex 环境加载的 `AGENTS.md` 为准；本 skill 不重复全局硬规则，只补充 Yudao 项目的公共执行方法。

## 与 Superpowers 的配合

当 `yudao` 被显式或隐式触发时，必须先执行 Superpowers 匹配检查，并使用匹配的 Superpowers skill。  
这不是可选建议；只要进入 `$yudao`，就先判断本次任务属于下面哪类，再按对应 workflow 执行。

- 新增功能、改行为、改流程前：`superpowers:brainstorming`
- 已有明确需求，需要整理实现步骤：`superpowers:writing-plans`
- 排查 bug、报错、状态异常、联调问题：`superpowers:systematic-debugging`
- 修改 skill / 规则文档：`superpowers:writing-skills`
- 准备宣称完成前：`superpowers:verification-before-completion`

执行要求：

- 不要因为用户没有显式写 `@superpowers` 就跳过 Superpowers 检查
- 如果任务命中多个 workflow，按最相关的 1 到 2 个执行，避免过度流程化
- 如果用户已经明确给出方案或要求直接落地，可以跳过不必要的设计扩展，但不能跳过对应的执行纪律
- 如果当前环境没有可用的 Superpowers skill，必须在回复中说明，并继续按 `$yudao` 本地规则执行

## 适用范围

适用于所有基于 Yudao / ruoyi-vue-pro 体系的项目，尤其是：

- Java Spring Boot 多模块后端
- Vue 管理台前端
- 需要联动 SQL、后端、前端的业务修改
- 需要梳理 Controller / Service / Mapper / DO / VO / API / View 链路的任务
- 需要先看代码再写方案、评估影响面、列出修改点的任务
- 需要梳理模块逻辑、给 PM / 测试 / 开发共同理解业务流程的任务
- 需要生成测试用例、测试点、Playwright 结构化场景清单的任务
- 明确要求使用 Yudao / ruoyi-vue-pro codegen、CRUD scaffold、单表 / 树表 / 主子表模板生成的任务

## 任务路由

进入 `$yudao` 后，先按任务类型决定参考文档：

- 先分析代码再写方案：
  读取 `references/plan-template.md`
- 梳理模块逻辑 / 给测试或 PM 讲清业务流程：
  读取 `references/module-logic-template.md`
- 生成测试用例 / 输出测试点 / 给 Playwright 梳理自动化场景：
  先读 `references/test-case-template.md`，必要时再读 `references/module-logic-template.md`
- Yudao codegen / CRUD scaffold / 单表 / 树表 / 主子表生成：
  读取 `references/codegen-workflow.md`

## 先看代码，再写方案

如果任务包含“分析代码”“梳理逻辑”“出方案”“评估改动”，先按下面顺序补齐上下文，再输出结论：

1. 定位功能所在模块。
2. 找到数据库表或核心数据来源。
3. 找到后端入口：Controller、Service、Mapper / DAL、DO、VO、Convert。
4. 找到前端入口：API、页面、弹窗、明细组件、字典来源。
5. 搜索同模块和全仓库相似实现，优先找“标准写法”。
6. 明确本次是改字段、改状态、改主子表、改权限、改字典、改导出，还是组合修改。
7. 识别风险点：事务、状态锁定、历史数据、主子表同步、前后端字段不一致、数据库约束。

不要在只读了一个文件或只看了接口名时直接写方案。

## Yudao 项目通用链路

默认按这条链路思考：

`SQL -> DO/VO -> Service -> Controller -> frontend API -> frontend View`

如果项目结构有差异，也仍然沿着“数据定义 -> 后端规则 -> 接口 -> 前端使用”的顺序排查。

## Codegen / CRUD 生成任务路由

只有当用户明确提到 Yudao / ruoyi-vue-pro codegen、代码生成、CRUD scaffold、单表生成、树表生成、主子表生成、模板生成时，才进入 codegen 路径。

普通业务逻辑修改、字段调整、状态锁定、前后端联调、权限配置，不默认走 codegen。

进入 codegen 路径后，优先读取详细流程：

- `references/codegen-workflow.md`

主 skill 只保留两个硬边界：

- 生成前必须确认生成类型、表结构、模板/配置、front-type、输出路径和覆盖风险
- 信息缺失、路径冲突或可能覆盖手写代码时，默认停止，不要猜着生成

## Yudao 分层约定

### Controller

- 负责接收参数、调用 Service、返回统一响应、挂权限/日志/导出注解。
- 不承载复杂业务逻辑。

### Service

- 承载业务校验、状态流转、事务边界、主子表同步、下游单据生成。
- “是否允许新增 / 修改 / 删除” 这类判断必须放在 Service。
- 关键状态锁定、是否已生成下游单据、是否允许继续编辑等逻辑必须以后端为准。

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

## 通用检查清单

### 改字段

默认联动检查：

- SQL 建表或字段定义
- DO / RespVO / SaveReqVO / PageReqVO
- Convert / Mapper 查询列
- 前端 interface、表单校验、表格列、详情展示
- 导入 / 导出 / 筛选条件 / 字典映射

### 改状态

默认联动检查：

- 状态字段定义和默认值
- Service 状态流转校验
- 错误码和提示语义
- 前端按钮显隐、可编辑态、列表展示、详情展示
- 是否影响下游单据生成、撤回、删除、关闭、审批等动作

### 改主子表

默认联动检查：

- 主表是否允许独立更新
- 明细是增量修改还是整体替换
- 明细新增 / 修改 / 删除是否有状态限制
- 生成下游单据后是否锁定来源单据
- 删除主表时是否联动清理明细

### 改权限 / 字典 / 导出

默认联动检查：

- 权限：`@PreAuthorize`、菜单权限标识、前端按钮权限
- 字典：后端值来源、前端选项、展示映射、筛选条件
- 导出：导出 VO、字典/枚举显示、筛选条件、导出列标题

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

本 skill 不覆盖全局 upgrade 约束，但在 Yudao 项目里要特别注意：

- 改表结构前，先确认需求是“改主建表 SQL”还是“明确要求 upgrade”
- 不要默认同时改主 SQL 和 upgrade
- 主子表、导入导出、历史数据兼容这类需求要单独确认边界

## ReturnCode 新增规则

新增 `new ReturnCode(...)` 前，必须先查重，不要只凭当前文件附近编号推断下一个号。

默认流程：

1. 先搜索是否已有相同或相近语义的错误码；如果已有，优先复用。
2. 如必须新增，扫描后端所有 `new ReturnCode(...)`，确认候选编号未被占用。
3. 在目标业务编号段内选择未使用的最小可用编号。
4. 新增后再次扫描，确认没有新增重复编号。

可使用通用只读脚本：

- macOS / zsh：`scripts/scan-return-codes.zsh`
- `scripts/scan-return-codes.ps1`

macOS / zsh 示例：

```zsh
zsh <yudao-skill>/scripts/scan-return-codes.zsh -Root <backend-root>
zsh <yudao-skill>/scripts/scan-return-codes.zsh -Root <backend-root> -Prefix 1_061_300
```

Windows / PowerShell 示例：

```powershell
powershell -ExecutionPolicy Bypass -File <yudao-skill>/scripts/scan-return-codes.ps1 -Root <backend-root>
powershell -ExecutionPolicy Bypass -File <yudao-skill>/scripts/scan-return-codes.ps1 -Root <backend-root> -Prefix 1_061_300
```

执行边界：

- 脚本只读扫描，不自动修改返回码
- 不要把重复码修复建立在肉眼判断上
- 最终只汇报实际扫描范围、重复结果和采用的编号

## 输出模板与边界

通用输出模板放在 `references/`：

- 方案模板：`references/plan-template.md`
- 模块逻辑梳理模板：`references/module-logic-template.md`
- 测试用例与 Playwright 场景模板：`references/test-case-template.md`

默认边界：

- 方案默认写链路、影响范围、改动点、风险、验证，不直接贴完整 Java / Vue / SQL
- 正式方案默认只保留最终设计结论，不保留推理痕迹、反向解释、排除理由或过程复盘
- 新增数据表时，方案默认写表职责、主从关系、关键字段、状态字段、关联字段、索引 / 约束建议、SQL 落点，不直接贴完整 `CREATE TABLE`
- 模块逻辑梳理默认先讲业务，再讲技术，兼顾 PM / 测试 / 开发
- 测试用例默认先出人工可读用例，再出 Playwright 结构化场景清单，不直接展开完整 Playwright 脚本

## 项目补充层

这个 skill 故意只写公共部分。

如果某个具体项目还有额外约定，应该在项目自己的文档或项目 skill 里补充，例如：

- 模块命名和目录差异
- 特殊状态机
- 特殊 SQL 目录
- 自定义审批、设备、IoT、流程或领域业务规则
- 项目独有的黄金参考实现

不要把这些项目私有规则回灌到公共 `yudao` skill 里。

## 结果汇报

任务完成时，尽量说明：

- 改了什么
- 为什么这么改
- 涉及了哪些 SQL / 后端 / 前端联动点
- 做了哪些验证
- 是否有仓库现存问题影响完整验证

## 验证分层

默认使用能覆盖本次改动的最小闭环验证，不要为了证明“完成”主动扩大验证范围。

后端默认优先级：

- 只改单业务模块：优先模块级编译，例如 `mvn -pl <module> -am -DskipTests compile`
- 只改局部类或配置：可先做定向编译、静态检查或人工 diff 核对
- 只有改公共框架、依赖、聚合配置或跨模块基础能力时，才考虑更大范围构建

前端默认优先级：

- 只改页面、弹窗、组件或 API 类型：优先单文件 lint、相关目录 lint、定向类型检查或人工 diff 核对
- 只有改构建配置、依赖、全局入口、路由聚合、全局组件注册、基础类型设施，或用户明确要求构建时，才运行 `pnpm build:*`
- 禁止把 `pnpm build:local` 作为普通前端改动的首选验证
- 只改样式、布局、高度、弹窗展示、表格滚动等 UI 局部表现时，不要运行 `pnpm build:*`，优先自查 diff、单文件 lint 或浏览器人工验证

汇报要求：

- 跑了轻量验证，就只说轻量验证通过
- 跑了模块编译，就只说模块编译通过
- 没有跑全量构建，不要暗示“全量构建通过”
- 如果为了节省时间没有跑重验证，要说明原因和剩余风险

## 使用原则

这个 skill 负责“Yudao 项目一般该怎么做”，不负责替代更高优先级规则。

- 与全局 `AGENTS.md` 冲突时，以全局规则为准
- 与用户当次明确要求冲突时，以用户要求为准
