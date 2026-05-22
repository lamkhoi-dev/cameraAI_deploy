<#
PowerShell helper to apply backend migrations (Windows).
Usage: Open PowerShell (with psql in PATH), then:
  .\apply_migration.ps1

#>
$migrationsDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$envVar = $env:DATABASE_URL
if (-not $envVar) {
    Write-Host "Environment variable DATABASE_URL not set. Please set it before running." -ForegroundColor Yellow
    exit 1
}

$sqlFile = Join-Path $migrationsDir "001_add_display_fields.sql"
if (-not (Test-Path $sqlFile)) {
    Write-Host "Migration SQL not found: $sqlFile" -ForegroundColor Red
    exit 1
}

Write-Host "Applying migration: $sqlFile" -ForegroundColor Cyan

# psql expects connection string - attempt to call it
$psql = "psql"
try {
    & $psql $envVar -f $sqlFile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "psql returned exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "Migration applied successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to run psql. Ensure PostgreSQL client is installed and psql is in PATH." -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}
