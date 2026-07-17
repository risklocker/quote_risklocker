$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root

$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$tmp = Join-Path $tempRoot ("risklocker-quotation-converter\pytest-" + [guid]::NewGuid().ToString("N"))
$resolvedTmp = [System.IO.Path]::GetFullPath($tmp)
if (-not $resolvedTmp.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Test temp path escaped the operating-system temp directory."
}
New-Item -ItemType Directory -Force -Path $resolvedTmp | Out-Null
$env:TEMP = $resolvedTmp
$env:TMP = $resolvedTmp
$env:PYTHONDONTWRITEBYTECODE = "1"

try {
    & ".\.venv\Scripts\python.exe" -m pytest -p no:cacheprovider
    if ($LASTEXITCODE -ne 0) {
        throw "Backend tests failed."
    }

    Set-Location (Join-Path $root "frontend")
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend production build failed."
    }
}
finally {
    Set-Location $root
    if (Test-Path -LiteralPath $resolvedTmp) {
        Remove-Item -LiteralPath $resolvedTmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}
