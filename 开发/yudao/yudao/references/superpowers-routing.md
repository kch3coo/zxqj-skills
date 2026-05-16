# Superpowers Routing

当 `yudao` 被显式或隐式触发时，先判断本次任务是否也命中 Superpowers workflow。

## 路由规则

- 新增功能、改行为、改流程前：`superpowers:brainstorming`
- 已有明确需求，需要整理实现步骤：`superpowers:writing-plans`
- 排查 bug、报错、状态异常、联调问题：`superpowers:systematic-debugging`
- 修改 skill / 规则文档：`superpowers:writing-skills`
- 准备宣称完成前：`superpowers:verification-before-completion`

## 执行边界

- 不要因为用户没有显式写 `@superpowers` 就跳过匹配检查。
- 如果任务命中多个 workflow，按最相关的 1 到 2 个执行，避免过度流程化。
- 如果用户已经明确给出方案或要求直接落地，可以跳过不必要的设计扩展，但不能跳过对应的执行纪律。
- 如果当前环境没有可用的 Superpowers skill，在回复中说明，并继续按 `$yudao` 本地规则执行。
