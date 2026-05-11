# Yudao Skill README

`yudao` 是所有 Yudao / ruoyi-vue-pro 风格项目的通用方法层。

它负责通用分析方式、分层约定、输出模板、测试模板和 codegen 流程；具体项目的路径、业务线、SQL 脚本和黄金参考实现，应放在项目自己的 skill 中。

## 核心定位

- 全局规则：由当前 Codex 环境的 `AGENTS.md` 兜底
- 通用芋道方法：由 `$yudao` 提供
- 项目差异：由项目 skill 提供

可以把它理解为：

`项目 skill = $yudao + 项目补充规则`

## 适用场景

- 分析 Yudao / ruoyi-vue-pro 项目代码
- 梳理模块逻辑
- 先分析再出方案
- 生成测试用例
- 为 Playwright 梳理结构化场景
- 处理 SQL、后端、前端联动修改
- 排查前后端联调、状态、数据库约束问题
- 处理 Yudao codegen / CRUD scaffold / 单表 / 树表 / 主子表生成

## 常用入口

- 主说明：
  - [SKILL.md](SKILL.md)
- 通用模板：
  - [plan-template.md](references/plan-template.md)
  - [module-logic-template.md](references/module-logic-template.md)
  - [test-case-template.md](references/test-case-template.md)
  - [codegen-workflow.md](references/codegen-workflow.md)
- 通用工具：
  - [scan-return-codes.ps1](scripts/scan-return-codes.ps1)

## 任务路由

### 1. 先分析再出方案

使用：

- `references/plan-template.md`

输出重点：

- 当前链路
- 影响范围
- 计划改动点
- 风险与边界
- 验证方式

默认不要把方案写成完整实现代码。

### 2. 梳理模块逻辑

使用：

- `references/module-logic-template.md`

输出重点：

- 先讲业务，再讲技术
- 兼顾 PM、测试、开发
- 写清入口、流程、规则、上下游、技术链路和测试关注点

### 3. 生成测试用例

使用：

- `references/test-case-template.md`

输出重点：

- 人工可读测试用例
- `P0 / P1 / P2` 优先级
- 数据准备
- 状态边界
- Playwright 可消费的结构化场景清单

默认不要直接展开完整 Playwright 脚本。

### 4. Codegen

使用：

- `references/codegen-workflow.md`

输出重点：

- 判断是否真的是 codegen 场景
- 区分单表、树表、主子表
- 检查表注释、字段注释、关联字段、front-type、输出路径
- 生成前预览文件集合
- 遇到 Hard Stop 条件时停止

### 5. ReturnCode 查重

新增错误码前，先使用通用只读脚本扫描：

```powershell
powershell -ExecutionPolicy Bypass -File <yudao-skill>/scripts/scan-return-codes.ps1 -Root <backend-root>
powershell -ExecutionPolicy Bypass -File <yudao-skill>/scripts/scan-return-codes.ps1 -Root <backend-root> -Prefix 1_061_300
```

输出重点：

- 是否存在重复编号
- 候选编号是否已被占用
- 指定编号段的下一个可用编号

脚本只读扫描，不自动修改项目文件。

## 与项目 Skill 的分工

`$yudao` 只放通用规则和通用模板。

项目 skill 负责补充：

- 项目仓库结构
- 项目启用模块
- 项目 SQL 脚本路径
- 项目业务线
- 移动端、IoT、设备等项目特有链路
- 项目黄金参考实现索引

不要把项目私有路径和业务规则写回 `$yudao`。

## 维护规则

- 新增通用模板，优先补 `$yudao/references`
- 新增项目路径、项目业务线、项目参考实现，放项目 skill
- `SKILL.md` 只放任务路由、硬边界、通用约定
- 详细模板和长流程放 `references/`
- 新增内容后检查绝对路径、失效路径、重复规则
- 如果某个 reference 继续变大，优先拆成更小的主题文件
