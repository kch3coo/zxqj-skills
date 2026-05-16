# ReturnCode Workflow

新增 `new ReturnCode(...)` 前，必须先查重，不要只凭当前文件附近编号推断下一个号。

## 默认流程

1. 先搜索是否已有相同或相近语义的错误码；如果已有，优先复用。
2. 如必须新增，扫描后端所有 `new ReturnCode(...)`，确认候选编号未被占用。
3. 在目标业务编号段内选择未使用的最小可用编号。
4. 新增后再次扫描，确认没有新增重复编号。

## 扫描脚本

可使用通用只读脚本：

- macOS / zsh：`scripts/scan-return-codes.zsh`
- Windows / PowerShell：`scripts/scan-return-codes.ps1`

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

## 执行边界

- 脚本只读扫描，不自动修改返回码。
- 不要把重复码修复建立在肉眼判断上。
- 最终只汇报实际扫描范围、重复结果和采用的编号。
