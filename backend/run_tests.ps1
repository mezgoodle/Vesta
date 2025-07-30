# FastAPI Test Runner Script

param(
    [Parameter(Position=0)]
    [ValidateSet("all", "unit", "integration", "performance", "main", "auth", "items", "users")]
    [string]$TestType = "all",
    
    [switch]$NoCoverage,
    [switch]$Verbose,
    [switch]$Install
)

function Install-TestDependencies {
    Write-Host "Installing test dependencies..." -ForegroundColor Green
    
    if (Test-Path "venv\Scripts\python.exe") {
        & "venv\Scripts\python.exe" -m pip install pytest pytest-asyncio coverage
    } else {
        python -m pip install pytest pytest-asyncio coverage
    }
}

function Run-Tests {
    param(
        [string]$Type,
        [bool]$WithCoverage,
        [bool]$IsVerbose
    )
    
    Write-Host "Running $Type tests..." -ForegroundColor Green
    
    # Build pytest command
    $cmd = @()
    
    if (Test-Path "venv\Scripts\python.exe") {
        $cmd += "venv\Scripts\python.exe"
    } else {
        $cmd += "python"
    }
    
    $cmd += "-m", "pytest"
    
    # Add verbosity
    if ($IsVerbose) {
        $cmd += "-v"
    } else {
        $cmd += "-q"
    }
    
    # Add coverage
    if ($WithCoverage) {
        $cmd += "--cov=app", "--cov=main", "--cov-report=html", "--cov-report=term-missing"
    }
    
    # Select test type
    switch ($Type) {
        "unit" { $cmd += "-m", "not integration and not performance" }
        "integration" { $cmd += "-m", "integration" }
        "performance" { $cmd += "-m", "performance" }
        "all" { $cmd += "tests/" }
        default { $cmd += "tests/test_$Type.py" }
    }
    
    Write-Host "Command: $($cmd -join ' ')" -ForegroundColor Yellow
    
    & $cmd[0] $cmd[1..($cmd.Length-1)]
}

function Show-Coverage {
    if (Test-Path "htmlcov\index.html") {
        Write-Host "`nCoverage report generated at: htmlcov\index.html" -ForegroundColor Green
        $openCoverage = Read-Host "Open coverage report in browser? (y/N)"
        if ($openCoverage -eq "y" -or $openCoverage -eq "Y") {
            Start-Process "htmlcov\index.html"
        }
    }
}

# Main execution
if ($Install) {
    Install-TestDependencies
    exit
}

Write-Host "FastAPI Test Runner" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan

$withCoverage = -not $NoCoverage

Run-Tests -Type $TestType -WithCoverage $withCoverage -IsVerbose $Verbose

if ($withCoverage) {
    Show-Coverage
}

Write-Host "`nTest execution completed!" -ForegroundColor Green
