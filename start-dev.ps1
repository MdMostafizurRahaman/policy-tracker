# Development startup script for Policy Tracker (Windows PowerShell)
# Run this script from the policy-tracker root directory

Write-Host "🚀 Starting Policy Tracker Development Environment" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Load environment variables from backend .env file
$envFile = ".\backend\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^#].+?)=(.+)$") {
            $name = $matches[1]
            $value = $matches[2].Trim('"')
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# Get configuration from environment
$backendHost = if ($env:BACKEND_HOST) { $env:BACKEND_HOST } else { "0.0.0.0" }
$backendPort = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { 8000 }
$frontendPort = if ($env:PORT) { $env:PORT } else { 3003 }
$apiUrl = if ($env:NEXT_PUBLIC_API_URL) { $env:NEXT_PUBLIC_API_URL } else { "http://localhost:8000/api" }

Write-Host "📊 Configuration:" -ForegroundColor Yellow
Write-Host "  Backend: http://$backendHost`:$backendPort" -ForegroundColor White
Write-Host "  Frontend: http://localhost:$frontendPort" -ForegroundColor White  
Write-Host "  API URL: $apiUrl" -ForegroundColor White
Write-Host ""

# Start backend
Write-Host "🔧 Starting Backend Server..." -ForegroundColor Blue
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\backend
    python main.py
}

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend
Write-Host "🌐 Starting Frontend Server..." -ForegroundColor Blue
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\frontend
    npm run dev
}

Write-Host ""
Write-Host "✅ Both servers starting..." -ForegroundColor Green
Write-Host "📊 Backend Job ID: $($backendJob.Id)" -ForegroundColor White
Write-Host "🌐 Frontend Job ID: $($frontendJob.Id)" -ForegroundColor White
Write-Host ""
Write-Host "🌍 Open http://localhost:$frontendPort in your browser" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 To stop both servers, press Ctrl+C or run:" -ForegroundColor Yellow
Write-Host "   Stop-Job $($backendJob.Id); Stop-Job $($frontendJob.Id)" -ForegroundColor White

# Monitor jobs
try {
    while ($true) {
        $backendState = Get-Job -Id $backendJob.Id | Select-Object -ExpandProperty State
        $frontendState = Get-Job -Id $frontendJob.Id | Select-Object -ExpandProperty State
        
        if ($backendState -eq "Failed" -or $frontendState -eq "Failed") {
            Write-Host "❌ One of the servers failed!" -ForegroundColor Red
            break
        }
        
        Start-Sleep -Seconds 5
    }
} finally {
    # Cleanup
    Stop-Job $backendJob.Id -ErrorAction SilentlyContinue
    Stop-Job $frontendJob.Id -ErrorAction SilentlyContinue
    Remove-Job $backendJob.Id -ErrorAction SilentlyContinue  
    Remove-Job $frontendJob.Id -ErrorAction SilentlyContinue
}
