# Yudao Skill README

`yudao` 是所有 Yudao / ruoyi-vue-pro 风格项目的通用方法层。

它负责通用分析方式、任务路由、输出模板、测试模板和 codegen 流程。具体项目的路径、业务线、SQL 脚本和黄金参考实现，应放在项目自己的 skill 中。

## 核心定位

- 全局规则：由当前 Codex 环境的 `AGENTS.md` 兜底
- 通用芋道方法：由 `$yudao` 提供
- 项目差异：由项目 skill 提供

可以把它理解为：

`项目 skill = $yudao + 项目补充规则`

## 文件结构

- `SKILL.md`：主入口，只保留触发、路由、默认链路和硬边界
- `references/superpowers-routing.md`：与 Superpowers workflow 的配合方式
- `references/layering-and-checklists.md`：Yudao 分层约定和联动检查清单
- `references/return-code-workflow.md`：ReturnCode 查重流程和扫描脚本说明
- `references/verification-policy.md`：后端 / 前端验证分层和汇报边界
- `references/plan-template.md`：先分析代码再写方案的输出模板
- `references/module-logic-template.md`：模块逻辑梳理模板
- `references/test-case-template.md`：测试用例和 Playwright 场景模板
- `references/codegen-workflow.md`：Yudao codegen / CRUD scaffold 流程
- `scripts/scan-return-codes.zsh`：macOS / zsh ReturnCode 只读扫描脚本
- `scripts/scan-return-codes.ps1`：Windows / PowerShell ReturnCode 只读扫描脚本
- `agents/openai.yaml`：agent 配置

## 维护规则

- `SKILL.md` 只放任务路由、硬边界、通用约定和 reference 指针。
- 长流程、模板、检查清单、脚本说明放 `references/`。
- 可重复执行的确定性动作放 `scripts/`。
- 项目私有路径、业务规则、SQL 目录、黄金参考实现放项目 skill。
- 新增 reference 后，在 `SKILL.md` 的路由表和本 README 的文件结构中补入口。
- 如果某个 reference 继续变大，优先按主题继续拆分。

## 适用场景

- 分析 Yudao / ruoyi-vue-pro 项目代码
- 梳理模块逻辑
- 先分析再出方案
- 生成测试用例
- 为 Playwright 梳理结构化场景
- 处理 SQL、后端、前端联动修改
- 排查前后端联调、状态、数据库约束问题
- 处理 Yudao codegen / CRUD scaffold / 单表 / 树表 / 主子表生成
