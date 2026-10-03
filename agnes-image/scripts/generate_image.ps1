# Agnes AI image generation (agnes-image-2.5-flash / 2.1-flash)
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File generate_image.ps1 -Json params.json
# Params JSON (UTF-8): prompt(required), model, size, ratio, image[](urls/data-uris),
#   return_base64(bool), out_dir, extras(object merged into request body)
# Prints "SAVED=<path>" per generated image. Exit 1 on failure with API error JSON.
param(
  [Parameter(Mandatory = $true)][string]$Json,
  [string]$OutDir
)
$ErrorActionPreference = 'Stop'

function Fail([string]$msg) { Write-Output $msg; exit 1 }

$key = $env:AGNES_API_KEY
if (-not $key -or [string]::IsNullOrWhiteSpace($key)) {
  Fail "MISSING_KEY: AGNES_API_KEY not set. Ask the user to run in their own terminal: setx AGNES_API_KEY `<their-key>` then reopen the session. Never accept the key pasted into chat."
}

if (-not (Test-Path -LiteralPath $Json)) { Fail "PARAMS_NOT_FOUND: $Json" }
try { $p = Get-Content -LiteralPath $Json -Raw -Encoding UTF8 | ConvertFrom-Json }
catch { Fail "BAD_JSON: $($_.Exception.Message)" }

$prompt = [string]$p.prompt
if (-not $prompt) { Fail "MISSING_PROMPT" }

$model   = if ($p.model) { [string]$p.model } else { "agnes-image-2.5-flash" }
$size    = if ($p.size)  { [string]$p.size }  else { "2K" }
$hasRatio = $p.PSObject.Properties['ratio'] -and $p.ratio
$ratio   = if ($hasRatio) { [string]$p.ratio } else { $null }
$returnBase64 = $false
if ($p.PSObject.Properties['return_base64']) { $returnBase64 = [bool]$p.return_base64 }
$images = @()
if ($p.image) { $images = @($p.image | ForEach-Object { [string]$_ }) }

$outDir = if ($p.PSObject.Properties['out_dir'] -and $p.out_dir) { [string]$p.out_dir }
          elseif ($OutDir) { $OutDir } else { "outputs\agnes-image" }

$body = [ordered]@{ model = $model; prompt = $prompt; size = $size }
if ($ratio) { $body.ratio = $ratio }
if ($returnBase64) { $body.return_base64 = $true }
if ($p.extras) {
  foreach ($prop in $p.extras.PSObject.Properties) { $body[$prop.Name] = $prop.Value }
}

# response_format MUST live in extra_body (top-level breaks the API)
$extra = [ordered]@{}
if ($p.extra_body) {
  foreach ($prop in $p.extra_body.PSObject.Properties) { $extra[$prop.Name] = $prop.Value }
}
if ($images.Count -gt 0) { $extra.image = [object[]]$images }
if (-not $extra.Contains('response_format')) {
  $extra.response_format = if ($returnBase64) { "b64_json" } else { "url" }
}
$body.extra_body = $extra

$uri = "https://apihub.agnes-ai.com/v1/images/generations"
$payload = [System.Text.Encoding]::UTF8.GetBytes(($body | ConvertTo-Json -Depth 8))
try {
  $resp = Invoke-RestMethod -Uri $uri -Method Post `
    -Headers @{ Authorization = "Bearer $key" } `
    -ContentType "application/json" -Body $payload -TimeoutSec 300
}
catch {
  $detail = if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $_.ErrorDetails.Message } else { $_.Exception.Message }
  Fail "API_ERROR: $detail"
}

New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$saved = 0
$index = 0
foreach ($item in @($resp.data)) {
  $index++
  if ($null -eq $item) { continue }
  $path = Join-Path $outDir ("agnes-image-{0}-{1}.png" -f $stamp, $index)
  if ($item.url) {
    Invoke-WebRequest -Uri $item.url -OutFile $path -UseBasicParsing -TimeoutSec 300 | Out-Null
  }
  elseif ($item.b64_json) {
    [System.IO.File]::WriteAllBytes($path, [Convert]::FromBase64String([string]$item.b64_json))
  }
  else { continue }
  $saved++
  Write-Output ("SAVED=" + (Resolve-Path -LiteralPath $path).Path)
}
if ($saved -eq 0) { Fail "NO_IMAGE_IN_RESPONSE: $($resp | ConvertTo-Json -Depth 6)" }
