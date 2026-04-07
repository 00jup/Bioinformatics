CONDA_ENV := bioinfo
VENV_DIR := .venv

# Windows에서 사용할 py launcher 버전 (override 가능: make data PY_VERSION=3.10)
PY_VERSION ?= 3.11

# ─────────────────────────────────────────────
# OS 감지 (Windows vs Unix)
# ─────────────────────────────────────────────
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    VENV_BIN := $(VENV_DIR)/Scripts
    EXE := .exe
else
    DETECTED_OS := $(shell uname -s 2>/dev/null || echo Unknown)
    VENV_BIN := $(VENV_DIR)/bin
    EXE :=
endif

# ─────────────────────────────────────────────
# 환경 자동 감지: venv → py(Windows) → conda
# ─────────────────────────────────────────────
ifneq ($(wildcard $(VENV_BIN)/python$(EXE)),)
    PYTHON := $(VENV_BIN)/python$(EXE)
    RUFF := $(VENV_BIN)/ruff$(EXE)
    ENV_NAME := venv
else ifeq ($(DETECTED_OS),Windows)
    PYTHON := py -$(PY_VERSION)
    RUFF := py -$(PY_VERSION) -m ruff
    ENV_NAME := py-$(PY_VERSION)
else
    PYTHON := conda run -n $(CONDA_ENV) python
    RUFF := conda run -n $(CONDA_ENV) ruff
    ENV_NAME := conda
endif

.PHONY: init init-conda init-venv init-py init-update format lint check data features train validate test predict all clean clean-env help

## ──────────────────────────────────────────────
## 환경 설정
## ──────────────────────────────────────────────

ifeq ($(DETECTED_OS),Windows)
init:
	@echo ========================================
	@echo  Windows 사용자: 다음 중 하나 직접 실행
	@echo ========================================
	@echo   make init-py        - py launcher로 직접 설치 (venv 없음, 가장 간단)
	@echo   make init-venv      - venv 격리 환경 생성
	@echo   make init-conda     - conda 사용
	@echo   .\setup.ps1         - PowerShell 직접 실행
else
init: ## 환경 설정 (conda 또는 venv 선택)
	@echo "========================================"
	@echo " 환경 선택"
	@echo "========================================"
	@echo "  1) conda  (anaconda/miniconda + environment.yml)"
	@echo "  2) venv   (python -m venv + requirements.txt)"
	@echo ""
	@read -p "선택 [1/2]: " choice; \
	case $$choice in \
		1) $(MAKE) init-conda ;; \
		2) $(MAKE) init-venv ;; \
		*) echo "❌ 잘못된 선택입니다."; exit 1 ;; \
	esac
endif

init-conda: ## conda 환경 생성 및 패키지 설치
	conda env create -f environment.yml
	conda run -n $(CONDA_ENV) python scripts/install_hooks.py
	@echo ========================================
	@echo  conda 환경 설정 완료!
	@echo  활성화: conda activate $(CONDA_ENV)
	@echo ========================================

# init-py: Windows 전용 - venv 없이 py launcher로 직접 설치
init-py: ## Windows: py launcher로 패키지 직접 설치 (venv 없음)
	py -$(PY_VERSION) -m pip install --upgrade pip
	py -$(PY_VERSION) -m pip install -r requirements.txt
	py -$(PY_VERSION) scripts/install_hooks.py
	@echo ========================================
	@echo  py -$(PY_VERSION) 환경 설정 완료!
	@echo  모든 make 명령이 'py -$(PY_VERSION)'로 실행됩니다
	@echo ========================================

ifeq ($(DETECTED_OS),Windows)
init-venv:
	@echo Detecting Python via py launcher (3.11 -^> 3.10 -^> 3.12)...
	py -3.11 -m venv $(VENV_DIR) || py -3.10 -m venv $(VENV_DIR) || py -3.12 -m venv $(VENV_DIR)
	$(VENV_BIN)/python$(EXE) -m pip install --upgrade pip
	$(VENV_BIN)/python$(EXE) -m pip install -r requirements.txt
	$(VENV_BIN)/python$(EXE) scripts/install_hooks.py
	@echo ========================================
	@echo  venv 환경 설정 완료!
	@echo  활성화 (cmd):        $(VENV_BIN)\activate.bat
	@echo  활성화 (PowerShell): $(VENV_BIN)\Activate.ps1
	@echo ========================================
else
init-venv: ## venv 환경 생성 및 패키지 설치 (python 3.10/3.11/3.12 필요)
	@VENV_PY="$$(command -v python3.10 2>/dev/null || command -v python3.11 2>/dev/null || command -v python3.12 2>/dev/null)"; \
	if [ -z "$$VENV_PY" ]; then \
		echo "❌ python3.10 / 3.11 / 3.12 중 하나가 필요합니다."; \
		echo "   설치 예시 (macOS): brew install python@3.11"; \
		echo "   설치 예시 (Ubuntu): sudo apt install python3.11 python3.11-venv"; \
		exit 1; \
	fi; \
	echo "✓ 사용할 Python: $$VENV_PY"; \
	"$$VENV_PY" -m venv $(VENV_DIR)
	$(VENV_BIN)/python$(EXE) -m pip install --upgrade pip
	$(VENV_BIN)/python$(EXE) -m pip install -r requirements.txt
	$(VENV_BIN)/python$(EXE) scripts/install_hooks.py
	@echo ""
	@echo "========================================"
	@echo " ✅ venv 환경 설정 완료!"
	@echo " 활성화: source $(VENV_DIR)/bin/activate"
	@echo "========================================"
endif

init-update: ## 환경 업데이트 (현재 활성 환경 기준)
ifeq ($(ENV_NAME),venv)
	$(VENV_BIN)/python$(EXE) -m pip install -r requirements.txt --upgrade
else ifeq ($(DETECTED_OS),Windows)
	py -$(PY_VERSION) -m pip install -r requirements.txt --upgrade
else
	conda env update -n $(CONDA_ENV) -f environment.yml --prune
endif

## ──────────────────────────────────────────────
## 코드 품질
## ──────────────────────────────────────────────

format: ## ruff로 코드 포맷팅
	$(RUFF) format src/ notebooks/

lint: ## ruff로 린트 검사
	$(RUFF) check src/

check: lint ## 포맷 + 린트 검사 (pre-push에서 사용)
	$(RUFF) format --check src/

## ──────────────────────────────────────────────
## 파이프라인
## ──────────────────────────────────────────────

data: ## 데이터 다운로드, 정제, train/validation/test 분할
	$(PYTHON) src/data_preparation.py

features: ## Feature 추출
	$(PYTHON) src/feature_engineering.py

train: ## Train set으로 모델 학습 + Validation 평가
	$(PYTHON) src/model_training.py

validate: ## Validation set으로 현재 모델 평가 (모델 조절용)
	$(PYTHON) -c "\
from src.model_training import load_split_data, evaluate_on_set, load_model_from_disk; \
import joblib; \
model = joblib.load('models/best_model.pkl'); \
X_val, y_val = load_split_data('validation', feature_set='B'); \
evaluate_on_set(model, X_val, y_val, 'Validation')"

test: ## Test set으로 최종 평가 (마지막에 1번만 실행)
	$(PYTHON) -c "\
from src.model_training import load_split_data, evaluate_on_set; \
import joblib; \
model = joblib.load('models/best_model.pkl'); \
X_test, y_test = load_split_data('test', feature_set='B'); \
evaluate_on_set(model, X_test, y_test, 'Test')"

predict: ## 예측 (usage: make predict INPUT=data/sample_input.csv)
	$(PYTHON) src/predict.py -f $(INPUT) $(if $(OUTPUT),-o $(OUTPUT)) $(if $(FORMAT),--format $(FORMAT))

all: data features train ## 전체 파이프라인 (data → features → train + validation)

## ──────────────────────────────────────────────
## 유틸리티
## ──────────────────────────────────────────────

clean: ## 생성된 파일 정리
	rm -rf data/raw/ data/processed/ data/train/ data/validation/ data/test/ models/*.pkl models/*.json results/figures/*.png
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

clean-env: ## 환경 삭제 (현재 활성 환경 기준)
ifeq ($(ENV_NAME),venv)
	$(PYTHON) -c "import shutil; shutil.rmtree('$(VENV_DIR)', ignore_errors=True)"
else ifneq ($(filter py-%,$(ENV_NAME)),)
	@echo "py 환경은 패키지 제거가 필요합니다: py -$(PY_VERSION) -m pip uninstall -r requirements.txt"
else
	conda env remove -n $(CONDA_ENV)
endif

help: ## 도움말 출력
	@echo "OS: $(DETECTED_OS) / 현재 활성 환경: $(ENV_NAME) / PY_VERSION: $(PY_VERSION)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
