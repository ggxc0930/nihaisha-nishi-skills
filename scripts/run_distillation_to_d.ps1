param(
  [string]$Source = "E:\倪海厦",
  [string]$OutputRoot = "D:\nihaisha-distillation",
  [string]$Python = "python",
  [int]$MaxPdfPages = 80
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$outputRootResolved = New-Item -ItemType Directory -Force -Path $OutputRoot
$work = Join-Path $outputRootResolved.FullName "distillation-output"
$plan = Join-Path $work "distillation-plan.jsonl"
$extracted = Join-Path $work "extracted-text"
$drafts = Join-Path $work "reference-drafts"
$localIndex = Join-Path $work "local-resource-index.jsonl"
$localInventory = Join-Path $work "local-resource-inventory.md"

Write-Host "Source: $Source"
Write-Host "Output: $work"

& $Python (Join-Path $repoRoot "scripts\index_local_resources.py") `
  --source $Source `
  --jsonl $localIndex `
  --markdown $localInventory

& $Python (Join-Path $repoRoot "scripts\build_distillation_plan.py") `
  --index $localIndex `
  --output $plan

& $Python (Join-Path $repoRoot "scripts\extract_text_corpus.py") `
  --plan $plan `
  --output-dir $extracted `
  --max-pdf-pages $MaxPdfPages

& $Python (Join-Path $repoRoot "scripts\build_distilled_reference.py") `
  --input-dir $extracted `
  --output-dir $drafts

Write-Host "Done. Drafts: $drafts"
