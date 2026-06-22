---
name: yudao-dev-workflow
description: 用于 Codex 独立处理 Yudao/ruoyi-vue-pro 企业后台开发任务：答疑、调研、代码实现、缺陷修复、前后端契约、Controller、Service、Mapper、Vue 页面、列表页、表格可拖动框线、主表列显示、外表 ID 可搜索分页下拉、分页下拉不显示裸 ID、操作列完整可点击且不固定右侧、金额和时间列排序、北京时间固定、移动端适配、响应式日期范围、SQL/DDL、权限、字典、状态流、主子表、导入导出、错误码、用户提示、验收规则、验证证据、评审包、开发文档和技能规则防漂移。
---

# Yudao 开发工作流

## 定位

这是一个独立的 Yudao 项目开发工作流技能，只负责开发阶段的答疑、调研、切片、实现、验证、评审和开发交付说明。

本技能不依赖 Yudao 插件、MCP 或历史上下文；用户当前轮明确要求使用其它能力时，才按用户要求切换。

本文件是入口导航，不承载规则正文。规则正文唯一来源是 `references/rule-registry.md`；其它 reference 只负责触发判断、流程、代码模式、模板、验收记录或检查清单。

## 职责分层

- `references/rule-registry.md`：唯一规则源，写“必须、不得、验收不通过、无法证明”。
- `references/gates.md`：判断本轮触发哪些规则 ID，不解释规则正文。
- `references/workflow.md`：定义开发推进流程、切片、边界和验证姿态。
- `references/frontend-template.md`：提供前端代码模式和落点，不新增规则。
- `references/acceptance.md`：记录证据和结论，不重新定义通过标准。
- `references/checklists.md`：执行前后自查，不替代规则验收。
- `references/templates.md`：输出模板，只放字段，不放新口径。
- `scripts/`：只做确定性扫描或查重，不替代人工判断。

## 核心原则

- 先读真实项目证据，再写方案或改代码。见 `CORE-001`。
- 只做当前请求的最小闭环切片，不顺手扩展相邻问题。见 `CORE-002`。
- 新增能力前先找已有能力和项目标准写法。见 `CORE-003`。
- 非平凡开发或修复前写执行清单，明确规则 ID、允许范围、验证边界和无法证明。见 `CORE-004`。
- 前后端契约、SQL、权限、字典、状态流、用户提示和前端固定规则按触发 ID 一起核对。
- 未执行的验证不能写成已通过；无法证明的范围必须明说。见 `CORE-005`。
- 保留用户已有改动，不自行恢复越界或无关改动。见 `CORE-006`。
- 修改本技能时，保持 `rule-registry.md` 为唯一事实源。见 `ARCH-001`。

## 使用顺序

1. 判断任务类型：答疑、调研、开发、修复、验证、开发文档、规则维护。
2. 答疑类任务只回答概念、规则或方案，不默认读项目、运行命令或改文件。
3. 调研类任务读取最小必要证据，只定位入口、影响面、已有能力和风险点。
4. 开发或修复前写执行清单：目标、当前切片、请求范围、允许修改面、禁止修改面、测试文件边界、触发规则 ID、允许验证、禁止验证、停止条件、无法证明。
5. 按“发现 -> 切片 -> 实施 -> 证明 -> 汇报”推进。
6. 交付前做三段检查：编辑前范围检查、编辑后越界检查、最终证据检查。
7. 修改技能规则或模板时，先维护规则唯一源，再做引用文件同步，最后运行防漂移检查。

## 按需读取

- 需要规则正文、硬边界、漏项或验收失败定义时，读 `references/rule-registry.md`。
- 需要调研、开发、修复、验证或交付时，读 `references/workflow.md`。
- 需要判断触发哪些规则 ID 时，读 `references/gates.md`。
- 涉及前端页面、列表、表格、弹窗、表单或按钮时，读 `references/frontend-template.md`。
- 判断是否达到交付标准时，读 `references/acceptance.md`。
- 需要输出计划、执行清单、影响面、契约差异、验证矩阵、评审包或开发文档时，读 `references/templates.md`。
- 交付前、边界审计或自查时，读 `references/checklists.md`。
- 新增或调整业务错误码时，可运行 `scripts/scan-return-codes.ps1` 做只读查重。
- 修改本技能后，运行 `scripts/check-skill-drift.ps1` 检查规则漂移。

## 规则索引

使用 `references/gates.md` 触发规则 ID，再到 `references/rule-registry.md` 读取正文。

- 核心：`ARCH-001`、`CORE-001`、`CORE-002`、`CORE-003`、`CORE-004`、`CORE-005`、`CORE-006`。
- 契约和后端：`CONTRACT-001`、`BACKEND-001`、`JAVA-001`、`ERROR-001`、`CODEGEN-001`。
- 前端：`FE-PAGE-001`、`FE-TABLE-001`、`FE-ACTION-001`、`FE-COLUMN-001`、`FE-FK-001`、`SORT-001`、`FE-TZ-001`、`FE-DATE-001`、`FE-MOBILE-001`、`FE-FORM-001`。
- 数据和业务：`SQL-001`、`PERM-001`、`DICT-001`、`FLOW-001`、`IMPORT-001`、`UX-001`。
- 测试和质量：`TEST-001`、`QUALITY-001`。

## 命令边界

默认可用：`git status`、`git diff`、`git diff --check`、`rg`、目标文件静态检查、契约引用扫描、错误码只读扫描、技能漂移扫描。

默认不自行运行：完整构建、完整类型检查、Maven 编译或打包、安装依赖、开发服务器、浏览器运行验证、运行时探测。需要这些证据时，先说明用途并取得用户当前轮明确授权。

## 技能维护

- 改规则正文：先改 `references/rule-registry.md`。
- 改触发条件：改 `references/gates.md`，并确认对应规则 ID 已存在。
- 改实现示例：改 `references/frontend-template.md` 或 `references/templates.md`，不要在示例里产生新规则。
- 改验收或清单：只改证据字段和检查动作，不改规则标准。
- 改完运行 `scripts/check-skill-drift.ps1` 和 `quick_validate.py`。

## 最终回复

最终回复必须区分：

- 已完成。
- 已执行验证。
- 未验证范围。
- 无法证明。
- 残余风险或阻塞项。
