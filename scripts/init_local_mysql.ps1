# Import DDL + seed into local MySQL.
# Usage:
#   .\scripts\init_local_mysql.ps1 -Password "your_root_password"
#   .\scripts\init_local_mysql.ps1 -User root -Password "xxx"

param(
  [string]$HostName = "127.0.0.1",
  [string]$Port = "3306",
  [string]$User = "root",
  [Parameter(Mandatory = $true)]
  [string]$Password,
  [string]$Database = "ai_assistant"
)

$ErrorActionPreference = "Stop"
$mysql = "C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe"
if (-not (Test-Path $mysql)) {
  $mysql = (Get-Command mysql -ErrorAction Stop).Source
}

$root = Split-Path -Parent $PSScriptRoot
$ddl = Join-Path $root "docs\mysql\ddl_v1.sql"
$seed = Join-Path $root "docs\mysql\seed_v1.sql"

function Invoke-MysqlFile([string]$File) {
  Write-Host "Applying: $File"
  Get-Content -Raw -Encoding UTF8 $File | & $mysql --host=$HostName --port=$Port --user=$User --password="$Password" --default-character-set=utf8mb4
  if ($LASTEXITCODE -ne 0) {
    throw "Failed applying $File (exit $LASTEXITCODE)"
  }
}

Invoke-MysqlFile $ddl
Invoke-MysqlFile $seed

Write-Host "OK. Tables in $Database :"
& $mysql --host=$HostName --port=$Port --user=$User --password="$Password" $Database -e "SHOW TABLES;"
