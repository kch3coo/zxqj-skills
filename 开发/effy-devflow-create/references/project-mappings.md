# Effy Project Mappings

Use this file before matching user nicknames, Effy users, business shorthand, stories, or repeated task concepts.

## User Nicknames

| shorthand | Effy nickname | user_id | notes |
| --- | --- | --- | --- |
| 佩奇 | 颜沛杰 | 144 | Confirmed by Anny on 2026-05-11. |
| 一安 | 陈一安 | 145 | Confirmed by Anny on 2026-05-11. |
| Walter | 杨健琦 | 143 | Confirmed by Anny on 2026-05-11. |
| Anny | 叶昱忻 | 142 | Confirmed by Anny on 2026-05-11. |

## Business Shorthand

| shorthand | canonical project / iteration / story | notes |
| --- | --- | --- |
| 会员 | 大谓面包 / 第二期 / part2会员系统 | Confirmed context: current scheduling only has this one membership system. |
| 销售联动生产计划 | Yian / 第三期 / 销售联动生产计划 | Effy story: `销售&库存&每日生产计划联动`. |
| 销售（不含联动）测试 | Yian / 第三期 / 采购+销售（不含联动） / 销售模块（不含联动）测试 | Effy story: `销售管理`; maps to completed tasks assigned to 佩奇/颜沛杰 for the sales non-linkage module test. |
| 小程序审批模块 | Yian / 第三期 / 小程序审批模块 | Effy story: `小程序 - 审批模块`. |
| 采购收货验货 | Yian / 第三期 / 采购+销售（不含联动） / 小程序采购收货验货 | Effy story: `小程序 - 采购管理`. |

## Deployment Naming Rule

Deployment task titles should follow the task date. Use `MMDD系统部署 - 项目/迭代说明` and update the title when the deployment date changes.

Deployment tasks should not use workflow. When creating a deployment task in Effy, set the assignee and date directly, leave workflow disabled, and verify `workflowEnabled=false`.
