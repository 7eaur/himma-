# Himma Local Services Startup Script
# Run this once to start all local services (Redis, MinIO)
# PostgreSQL 18 starts automatically as Windows Service

param(
    [switch]$Stop
)

if ($Stop) {
    Write-Host "Stopping services..."
    Get-Process minio -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process "redis-server" -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "Services stopped."
    exit
}

Write-Host "===== Starting Himma Local Services =====" -ForegroundColor Cyan

# 1. Redis
$redisProc = Get-Process "redis-server" -ErrorAction SilentlyContinue
if ($redisProc) {
    Write-Host "[Redis]   Already running (PID $($redisProc.Id))" -ForegroundColor Green
} else {
    Start-Process -FilePath "C:\himma-services\redis\redis-server.exe" -WindowStyle Hidden
    Start-Sleep -Seconds 2
    $ping = & "C:\himma-services\redis\redis-cli.exe" ping 2>&1
    if ($ping -eq "PONG") {
        Write-Host "[Redis]   Started OK" -ForegroundColor Green
    } else {
        Write-Host "[Redis]   FAILED to start" -ForegroundColor Red
    }
}

# 2. MinIO
$minioProc = Get-Process minio -ErrorAction SilentlyContinue
if ($minioProc) {
    Write-Host "[MinIO]   Already running (PID $($minioProc.Id))" -ForegroundColor Green
} else {
    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = "C:\himma-services\minio\minio.exe"
    $pinfo.Arguments = "server C:\himma-services\minio-data --console-address :9001 --address :9000"
    $pinfo.UseShellExecute = $false
    $pinfo.CreateNoWindow = $true
    $pinfo.EnvironmentVariables["MINIO_ROOT_USER"] = "minioadmin"
    $pinfo.EnvironmentVariables["MINIO_ROOT_PASSWORD"] = "minioadmin"
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $pinfo
    $proc.Start() | Out-Null
    Start-Sleep -Seconds 4
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:9000/minio/health/live" -UseBasicParsing -TimeoutSec 5
        Write-Host "[MinIO]   Started OK (PID $($proc.Id), Console: http://localhost:9001)" -ForegroundColor Green
    } catch {
        Write-Host "[MinIO]   FAILED to start: $_" -ForegroundColor Red
    }
}

# 3. PostgreSQL (Windows Service — should already be running)
$pgService = Get-Service -Name "postgresql-x64-18" -ErrorAction SilentlyContinue
if ($pgService -and $pgService.Status -eq "Running") {
    Write-Host "[PostgreSQL] Running as Windows Service" -ForegroundColor Green
} else {
    Write-Host "[PostgreSQL] Not running — start it via Services or pgAdmin" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "===== Service URLs =====" -ForegroundColor Cyan
Write-Host "PostgreSQL : postgresql://himma:himmapass@localhost:5432/himma_db"
Write-Host "Redis      : redis://localhost:6379/0"
Write-Host "MinIO API  : http://localhost:9000"
Write-Host "MinIO UI   : http://localhost:9001  (minioadmin / minioadmin)"
Write-Host "FastAPI    : http://localhost:8000  (run: .\scripts\start-api.ps1)"
Write-Host "Next.js    : http://localhost:3000  (run: cd apps/web && npm run dev)"
