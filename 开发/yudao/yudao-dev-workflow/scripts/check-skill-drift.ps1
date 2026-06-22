param(
  [string]$SkillRoot
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($SkillRoot)) {
  $SkillRoot = Split-Path -Parent $PSScriptRoot
}

$SkillRoot = [System.IO.Path]::GetFullPath($SkillRoot)
$registryPath = Join-Path $SkillRoot 'references\rule-registry.md'
$issues = New-Object System.Collections.Generic.List[string]

function Read-Utf8Text([string]$Path) {
  return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
}

function Add-Issue([string]$Message) {
  $issues.Add($Message) | Out-Null
}

function Get-RelativeSkillPath([string]$BasePath, [string]$FullPath) {
  $baseFull = [System.IO.Path]::GetFullPath($BasePath).TrimEnd('\') + '\'
  $targetFull = [System.IO.Path]::GetFullPath($FullPath)
  if ($targetFull.StartsWith($baseFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $targetFull.Substring($baseFull.Length)
  }
  return $targetFull
}

if (-not (Test-Path -LiteralPath $registryPath)) {
  Add-Issue "Missing rule registry: $registryPath"
} else {
  $registryText = Read-Utf8Text $registryPath
}

$requiredRuleIds = @(
  'ARCH-001',
  'CORE-001',
  'CORE-002',
  'CORE-003',
  'CORE-004',
  'CORE-005',
  'CORE-006',
  'CONTRACT-001',
  'BACKEND-001',
  'FE-PAGE-001',
  'FE-TABLE-001',
  'FE-ACTION-001',
  'FE-COLUMN-001',
  'FE-FK-001',
  'SORT-001',
  'FE-TZ-001',
  'FE-DATE-001',
  'FE-MOBILE-001',
  'FE-FORM-001',
  'SQL-001',
  'PERM-001',
  'DICT-001',
  'FLOW-001',
  'IMPORT-001',
  'UX-001',
  'TEST-001',
  'QUALITY-001',
  'ERROR-001',
  'JAVA-001',
  'CODEGEN-001'
)

if ($registryText) {
  foreach ($ruleId in $requiredRuleIds) {
    if ($registryText -notmatch "(?m)^##\s+$([regex]::Escape($ruleId))\b") {
      Add-Issue "rule-registry.md missing rule id: $ruleId"
    }
  }
}

$requiredReferenceFiles = @(
  'SKILL.md',
  'references\gates.md',
  'references\acceptance.md',
  'references\checklists.md',
  'references\frontend-template.md',
  'references\templates.md'
)

foreach ($relativePath in $requiredReferenceFiles) {
  $path = Join-Path $SkillRoot $relativePath
  if (-not (Test-Path -LiteralPath $path)) {
    Add-Issue "Missing file: $relativePath"
    continue
  }
  $text = Read-Utf8Text $path
  if ($text -notmatch 'rule-registry\.md') {
    Add-Issue "$relativePath does not reference rule-registry.md"
  }
}

$forbiddenPatterns = @(
  @{ Pattern = '\u4f7f\u7528[\u201c"]\u66f4\u591a[\u201d"]\u4e0b\u62c9\u6216'; Message = 'Old action-button wording: more dropdown as an option' },
  @{ Pattern = '\u66f4\u591a\u4e0b\u62c9\u3001\u6362\u884c'; Message = 'Old action-button wording: more dropdown grouped with wrapping' },
  @{ Pattern = '\u8fdb\u5165\u66f4\u591a\u4e0b\u62c9'; Message = 'Old action-button wording: actions can enter more dropdown' },
  @{ Pattern = '\u624b\u673a\u7aef\u9002\u914d\u662f\u4f18\u5316\u9879'; Message = 'Old mobile wording: mobile adaptation as optimization' },
  @{ Pattern = '\u4e1a\u52a1\u65f6\u533a.*(\u53ef\u9009|\u53ef\u914d|\u8ddf\u968f\u6d4f\u89c8\u5668|\u8ddf\u968f\u7cfb\u7edf)'; Message = 'Old timezone wording: business timezone configurable or local-following' },
  @{ Pattern = '\u6240\u6709\u5305\u542b\u4e1a\u52a1\u6570\u636e\u8868\u683c\u7684\u9875\u9762\u63d0\u4f9b[\u201c"]\u5217\u663e\u793a[\u201d"]\u64cd\u4f5c'; Message = 'Old column wording: every business table page provides column visibility' },
  @{ Pattern = '\u6bcf\u5f20\u4e1a\u52a1\u6570\u636e\u8868\u683c\u90fd\u6709\u5bf9\u5e94\u5217\u914d\u7f6e'; Message = 'Old column wording: every business table has column config' },
  @{ Pattern = '\u540c\u9875\u591a\u5f20\u4e1a\u52a1\u8868\u683c\u4e0d\u5f97\u6f0f\u914d'; Message = 'Old column wording: multi-table pages must configure every business table' },
  @{ Pattern = '\u591a\u8868\u9875\u9762\u5fc5\u987b\u4e3a\u6bcf\u5f20\u4e1a\u52a1\u8868\u683c\u62c6\u5206\s*key'; Message = 'Old column key wording: one key per business table' },
  @{ Pattern = 'pageSize\s*\u56fa\u5b9a\s*20|\u56fa\u5b9a\s*pageSize\s*[:\uff1a]?\s*20|\u9ed8\u8ba4\u5206\u9875\u4e0d\u662f\s*20|\u9ed8\u8ba4\u8fdc\u7a0b\u5206\u9875\u662f\u5426\u4e3a\s*`?pageNo:\s*1`?.*`?pageSize:\s*20`?|\u9ed8\u8ba4\s*pageSize\s*[:\uff1a]\s*20'; Message = 'Old FK pagination wording: pageSize fixed to exactly 20' },
  @{ Pattern = '<el-table-column[^\r\n]*label="操作"[^\r\n]*fixed="right"|<el-table-column[^\r\n]*fixed="right"[^\r\n]*label="操作"'; Message = 'Old action-column code: fixed right operation column' }
)

$scanFiles = Get-ChildItem -LiteralPath $SkillRoot -Recurse -File -Include '*.md','*.yaml','*.yml' |
  Where-Object { $_.FullName -ne $registryPath }

foreach ($file in $scanFiles) {
  $relative = Get-RelativeSkillPath $SkillRoot $file.FullName
  $text = Read-Utf8Text $file.FullName
  foreach ($item in $forbiddenPatterns) {
    if ($text -match $item.Pattern) {
      Add-Issue "$relative matched drift check: $($item.Message)"
    }
  }
}

if ($issues.Count -gt 0) {
  Write-Host 'Skill drift check failed:'
  foreach ($issue in $issues) {
    Write-Host "- $issue"
  }
  exit 1
}

Write-Host 'Skill drift check passed.'
