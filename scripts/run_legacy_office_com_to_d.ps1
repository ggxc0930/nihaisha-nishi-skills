param(
  [string]$Plan = "D:\nihaisha-distillation\distillation-output\distillation-plan.jsonl",
  [string]$OutputDir = "D:\nihaisha-distillation\distillation-output\extracted-text",
  [string]$Python = "python",
  [int]$Start = 0,
  [int]$Limit = 0,
  [int]$TimeoutSeconds = 90,
  [string]$Report = "D:\nihaisha-distillation\distillation-output\legacy-office-runner-report.jsonl"
)

$ErrorActionPreference = "Stop"

function Write-JsonLine($Path, $Object) {
  $json = $Object | ConvertTo-Json -Compress -Depth 8
  Add-Content -LiteralPath $Path -Value $json -Encoding UTF8
}

$items = Get-Content -LiteralPath $Plan -Encoding UTF8 |
  Where-Object { $_.Trim() } |
  ForEach-Object { $_ | ConvertFrom-Json } |
  Where-Object { $_.action -eq "convert-first" -and @(".doc", ".ppt") -contains ([string]$_.extension).ToLowerInvariant() }

$end = if ($Limit -gt 0) { [Math]::Min($items.Count, $Start + $Limit) } else { $items.Count }

for ($index = $Start; $index -lt $end; $index++) {
  $item = $items[$index]
  $started = Get-Date
  $singleReport = Join-Path (Split-Path -Parent $Report) ("legacy-office-single-{0:D5}.jsonl" -f $index)
  $args = @(
    "scripts\extract_legacy_office_com.py",
    "--plan", $Plan,
    "--output-dir", $OutputDir,
    "--report", $singleReport,
    "--extensions", ".doc,.ppt",
    "--start", [string]$index,
    "--limit", "1",
    "--skip-existing"
  )

  $process = Start-Process -FilePath $Python -ArgumentList $args -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru
  $completed = $process.WaitForExit($TimeoutSeconds * 1000)
  if ($completed) {
    Write-JsonLine $Report ([ordered]@{
      status = "completed"
      index = $index
      exit_code = $process.ExitCode
      relative_path = $item.relative_path
      single_report = $singleReport
    })
  } else {
    try { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue } catch {}
    Get-Process WINWORD,POWERPNT -ErrorAction SilentlyContinue |
      Where-Object { $_.StartTime -ge $started.AddSeconds(-2) } |
      ForEach-Object {
        try { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {}
      }
    Write-JsonLine $Report ([ordered]@{
      status = "timeout"
      index = $index
      timeout_seconds = $TimeoutSeconds
      relative_path = $item.relative_path
    })
  }
}

Write-Host "processed-indexes $Start..$($end - 1)"
Write-Host "report=$Report"
