# setup.ps1 - DILI 프로젝트 venv 설정 (Windows 전용)
# 사용법:
#   PowerShell> .\setup.ps1
#
# 만약 실행 정책 오류가 나면:
#   PowerShell> powershell -ExecutionPolicy Bypass -File .\setup.ps1

$ErrorActionPreference = "Stop"

$VenvDir = ".venv"
$RequiredVersions = @("3.11", "3.10", "3.12")

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " bioinformatics venv 설정 (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ─────────────────────────────────────────────
# 1) Python 3.10/3.11/3.12 탐지 (py launcher 우선)
# ─────────────────────────────────────────────
$PyArgs = $null

# py launcher 사용 가능 여부
$pyAvailable = $false
try {
    & py --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $pyAvailable = $true }
} catch {}

if ($pyAvailable) {
    foreach ($ver in $RequiredVersions) {
        $check = & py "-$ver" --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Python $ver 발견 (py launcher): $check" -ForegroundColor Green
            $PyArgs = @("-$ver")
            break
        }
    }
}

# py launcher 없으면 python 직접 확인
if (-not $PyArgs) {
    try {
        $check = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $verStr = ($check -split ' ')[1]
            $verShort = ($verStr -split '\.')[0..1] -join '.'
            if ($RequiredVersions -contains $verShort) {
                Write-Host "✓ Python $verShort 발견: $check" -ForegroundColor Green
                $PyArgs = @()
            } else {
                Write-Host "⚠ python = $check (3.10/3.11/3.12 필요)" -ForegroundColor Yellow
            }
        }
    } catch {}
}

if ($null -eq $PyArgs) {
    Write-Host ""
    Write-Host "❌ Python 3.10 / 3.11 / 3.12 / 3.13 중 하나가 필요합니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "  설치 방법 (권장):"
    Write-Host "    1. https://www.python.org/downloads/"
    Write-Host "       'Add python.exe to PATH' 체크 + py launcher 함께 설치"
    Write-Host "    2. 또는 winget install Python.Python.3.13"
    exit 1
}

# ─────────────────────────────────────────────
# 2) 기존 venv 처리
# ─────────────────────────────────────────────
if (Test-Path $VenvDir) {
    Write-Host ""
    Write-Host "기존 $VenvDir 폴더가 있습니다. 삭제하고 새로 만들까요? [Y/n]: " -NoNewline -ForegroundColor Yellow
    $answer = Read-Host
    if ($answer -eq "" -or $answer -eq "Y" -or $answer -eq "y") {
        Remove-Item -Recurse -Force $VenvDir
        Write-Host "  → 기존 폴더 삭제 완료"
    } else {
        Write-Host "취소됨"
        exit 0
    }
}

# ─────────────────────────────────────────────
# 3) venv 생성
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "venv 생성 중..."
if ($PyArgs.Count -gt 0) {
    & py @PyArgs -m venv $VenvDir
} else {
    & python -m venv $VenvDir
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ venv 생성 실패" -ForegroundColor Red
    exit 1
}

# ─────────────────────────────────────────────
# 4) 패키지 설치
# ─────────────────────────────────────────────
$VenvPython = "$VenvDir\Scripts\python.exe"
$VenvPip = "$VenvDir\Scripts\pip.exe"

Write-Host ""
Write-Host "pip 업그레이드..."
& $VenvPython -m pip install --upgrade pip

Write-Host ""
Write-Host "패키지 설치 중 (몇 분 걸립니다)..."
& $VenvPip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 패키지 설치 실패" -ForegroundColor Red
    exit 1
}

# ─────────────────────────────────────────────
# 5) git hook 설치
# ─────────────────────────────────────────────
if (Test-Path ".git") {
    New-Item -Path ".git\hooks" -ItemType Directory -Force | Out-Null
    Copy-Item "hooks\pre-push" ".git\hooks\pre-push" -Force
    Write-Host "✓ pre-push hook 설치됨"
}

# ─────────────────────────────────────────────
# 6) 완료 안내
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " ✅ venv 설정 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "환경 활성화:"
Write-Host "  PowerShell> .\.venv\Scripts\Activate.ps1"
Write-Host "  cmd>        .venv\Scripts\activate.bat"
Write-Host ""
Write-Host "파이프라인 실행 (venv 활성화 후):"
Write-Host "  python src\data_preparation.py"
Write-Host "  python src\feature_engineering.py"
Write-Host "  python src\model_training.py"
Write-Host "  python src\predict.py -f data\sample_input.csv"
Write-Host ""
Write-Host "또는 활성화 없이 직접:"
Write-Host "  .\.venv\Scripts\python.exe src\data_preparation.py"
Write-Host ""
