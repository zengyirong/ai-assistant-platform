# Build production images when Docker containers cannot reach the internet.
# Host OS must have Node/pnpm and Python 3.11+ with network access.
#
# Usage (from repo root, PowerShell):
#   .\scripts\build-prod-images.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> [1/4] Frontend: pnpm build:ele (host)" -ForegroundColor Cyan
$envFile = @"
VITE_BASE=/
VITE_GLOB_API_URL=/api/v1
VITE_COMPRESS=none
VITE_PWA=false
VITE_ROUTER_HISTORY=hash
VITE_INJECT_APP_LOADING=true
VITE_ARCHIVER=false
"@
Set-Content -Encoding utf8 -Path "frontend\apps\web-ele\.env.production.local" -Value $envFile
Push-Location frontend
pnpm run build:ele
if ($LASTEXITCODE -ne 0) { throw "frontend build failed" }
Pop-Location

if (-not (Test-Path "frontend\apps\web-ele\dist\index.html")) {
  throw "frontend dist missing: frontend/apps/web-ele/dist"
}

Write-Host "==> [2/4] Backend: download Linux wheels on host" -ForegroundColor Cyan
$wheels = Join-Path $Root "backend\wheels"
New-Item -ItemType Directory -Force -Path $wheels | Out-Null
Remove-Item "$wheels\*" -Force -ErrorAction SilentlyContinue

python -m pip download `
  -d $wheels `
  -r "backend\requirements-prod.txt" `
  --platform manylinux2014_x86_64 `
  --python-version 311 `
  --implementation cp `
  --abi cp311 `
  --only-binary=:all: `
  --no-deps `
  -i https://pypi.tuna.tsinghua.edu.cn/simple

if ($LASTEXITCODE -ne 0) { throw "pip download failed" }

Write-Host "==> [3/4] Docker build frontend (prebuilt dist)" -ForegroundColor Cyan
docker compose -f docker-compose.prod.yml --env-file .env.prod build frontend
if ($LASTEXITCODE -ne 0) { throw "frontend image build failed" }

Write-Host "==> [4/4] Docker build backend (offline wheels)" -ForegroundColor Cyan
docker compose -f docker-compose.prod.yml --env-file .env.prod build backend
if ($LASTEXITCODE -ne 0) { throw "backend image build failed" }

Write-Host "==> Done. Images:" -ForegroundColor Green
docker images aap-frontend:prod
docker images aap-backend:prod
Write-Host ""
Write-Host "Next: docker save aap-frontend:prod aap-backend:prod -o aap-images.tar"
