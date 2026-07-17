$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$envFile = Join-Path $root ".env"
$migrationRoot = Join-Path $root "migrations"

if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
    throw "psql is required to apply migrations. Install PostgreSQL command-line tools first."
}
if (-not (Test-Path -LiteralPath $envFile)) {
    throw ".env was not found in the project root."
}

$databaseLine = Get-Content -LiteralPath $envFile |
    Where-Object { $_ -match '^DATABASE_URL=' } |
    Select-Object -First 1
if (-not $databaseLine) {
    throw "DATABASE_URL is required in .env."
}
$databaseUrl = $databaseLine.Substring("DATABASE_URL=".Length).Trim()
if ($databaseUrl -notmatch '^postgres(?:ql)?://') {
    throw "DATABASE_URL must be a Supabase/Postgres connection string."
}

$migrations = Get-ChildItem -LiteralPath $migrationRoot -Filter "*.sql" -File | Sort-Object Name
foreach ($migration in $migrations) {
    Write-Host "Applying $($migration.Name)..."
    & psql $databaseUrl -v ON_ERROR_STOP=1 -f $migration.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Migration failed: $($migration.Name)"
    }
}
Write-Host "All ordered migrations applied successfully."
