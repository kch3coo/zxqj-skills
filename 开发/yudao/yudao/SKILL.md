---
name: yudao
description: Use when working on Yudao, 芋道, ruoyi-vue-pro, or 若依风格 projects, especially for 代码梳理, 写方案, 测试用例, Playwright 场景, API or SQL changes, form/field linkage, dictionary/error-code updates, main-detail flows, status transitions, frontend-backend debugging, database constraints, codegen, or tracing Controller/Service/Mapper/DO/VO/API/View chains.
---

# Yudao Common Execution Guide

这个 skill 是所有 Yudao / ruoyi-vue-pro 项目的通用方法层。
它不绑定具体仓库，只提供跨项目适用的分析路径、任务路由、硬边界和 reference 入口。

全局底线仍以当前 Codex 环境加载的 `AGENTS.md` 为准；本 skill 不重复全局硬规则，只补充 Yudao 项目的公共执行方法。

## 先做路由

进入 `$yudao` 后，先判断任务类型，再只读取相关 reference：

| 任务类型 | 读取 |
| --- | --- |
| 需要配合 Superpowers workflow | `references/superpowers-routing.md` |
| 先分析代码再写方案 | `references/plan-template.md` |
| 梳理模块逻辑 / 给测试或 PM 讲清业务流程 | `references/module-logic-template.md` |
| 生成测试用例 / 测试点 / Playwright 场景 | `references/test-case-template.md`，必要时再读 `references/module-logic-template.md` |
| Yudao codegen / CRUD scaffold / 单表 / 树表 / 主子表生成 | `references/codegen-workflow.md` |
| 字段、状态、主子表、权限、字典、导出等联动修改 | `references/layering-and-checklists.md` |
| 新增或调整 ReturnCode / ErrorCode | `references/return-code-workflow.md` |
| 准备汇报完成、选择验证命令 | `references/verification-policy.md` |
| 本地启动 / 重启项目、自动错开前后端端口、启动数据库依赖、重置 MySQL volume | 使用 `yudao-start` skill，不在 `$yudao` 里展开启动流程 |

如果任务命中多个类型，优先读取直接相关的 1 到 2 个 reference，避免把全部规则一次性加载进上下文。

## 默认分析链路

Yudao 项目默认按这条链路思考：

`SQL -> DO/VO -> Service -> Controller -> frontend API -> frontend View`

如果项目结构有差异，也沿着“数据定义 -> 后端规则 -> 接口 -> 前端使用”的顺序排查。

## 先看代码，再写方案

如果任务包含“分析代码”“梳理逻辑”“出方案”“评估改动”，先补齐这些上下文：

1. 定位功能所在模块。
2. 找到数据库表或核心数据来源。
3. 找到后端入口：Controller、Service、Mapper / DAL、DO、VO、Convert。
4. 找到前端入口：API、页面、弹窗、明细组件、字典来源。
5. 搜索同模块和全仓库相似实现，优先找标准写法。
6. 明确本次是改字段、改状态、改主子表、改权限、改字典、改导出，还是组合修改。
7. 识别风险点：事务、状态锁定、历史数据、主子表同步、前后端字段不一致、数据库约束。

不要在只读了一个文件或只看了接口名时直接写方案。

## Codegen 硬边界

只有当用户明确提到 Yudao / ruoyi-vue-pro codegen、代码生成、CRUD scaffold、单表生成、树表生成、主子表生成、模板生成时，才进入 codegen 路径。

普通业务逻辑修改、字段调整、状态锁定、前后端联调、权限配置，不默认走 codegen。

进入 codegen 路径后，读取 `references/codegen-workflow.md`。主 skill 只保留两个硬边界：

- 生成前必须确认生成类型、表结构、模板 / 配置、front-type、输出路径和覆盖风险。
- 信息缺失、路径冲突或可能覆盖手写代码时，默认停止，不要猜着生成。

## 输出边界

默认输出遵守：

- 方案写链路、影响范围、改动点、风险、验证，不直接贴完整 Java / Vue / SQL。
- 正式方案只保留最终设计结论，不保留推理痕迹、反向解释、排除理由或过程复盘。
- 新增数据表时，方案写表职责、主从关系、关键字段、状态字段、关联字段、索引 / 约束建议、SQL 落点，不直接贴完整 `CREATE TABLE`。
- 模块逻辑梳理先讲业务，再讲技术，兼顾 PM / 测试 / 开发。
- 测试用例先出人工可读用例，再出 Playwright 结构化场景清单，不直接展开完整 Playwright 脚本。

## 项目补充层

这个 skill 故意只写公共部分。

如果某个具体项目还有额外约定，放在项目自己的文档或项目 skill 里，例如：

- 模块命名和目录差异
- 特殊状态机
- 特殊 SQL 目录
- 自定义审批、设备、IoT、流程或领域业务规则
- 项目独有的黄金参考实现

不要把项目私有规则回灌到公共 `yudao` skill 里。

## 使用原则

- 与全局 `AGENTS.md` 冲突时，以全局规则为准。
- 与用户当次明确要求冲突时，以用户要求为准。
- 任务完成时，说明改了什么、涉及哪些 SQL / 后端 / 前端联动点、做了哪些验证，以及是否有仓库现存问题影响完整验证。
