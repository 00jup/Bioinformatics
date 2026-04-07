CONDA_ENV := bioinfo
VENV_DIR := .venv

# venv 생성용 Python 자동 탐지 (3.10 → 3.11 → 3.12)
# 3.13+ 는 일부 패키지 빌드 실패하므로 제외
VENV_PYTHON := $(shell command -v python3.10 2>/dev/null || command -v python3.11 2>/dev/null || command -v python3.12 2>/dev/null)

# 환경 자동 감지: .venv가 있으면 venv 우선, 없으면 conda
ifneq ($(wildcard $(VENV_DIR)/bin/python),)
    PYTHON := $(VENV_DIR)/bin/python
    RUFF := $(VENV_DIR)/bin/ruff
    ENV_NAME := venv
else
    PYTHON := conda run -n $(CONDA_ENV) python
    RUFF := conda run -n $(CONDA_ENV) ruff
    ENV_NAME := conda
endif

.PHONY: init init-conda init-venv _install-hooks init-update format lint check data features train validate test predict all clean clean-env help

## ──────────────────────────────────────────────
## 환경 설정
## ──────────────────────────────────────────────

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

init-conda: ## conda 환경 생성 및 패키지 설치
	conda env create -f environment.yml
	@$(MAKE) _install-hooks
	@echo ""
	@echo "========================================"
	@echo " ✅ conda 환경 설정 완료!"
	@echo " 활성화: conda activate $(CONDA_ENV)"
	@echo "========================================"

init-venv: ## venv 환경 생성 및 패키지 설치 (python 3.10/3.11/3.12 필요)
	@if [ -z "$(VENV_PYTHON)" ]; then \
		echo "❌ python3.10 / 3.11 / 3.12 중 하나가 필요합니다."; \
		echo "   설치 예시 (macOS): brew install python@3.11"; \
		echo "   설치 예시 (Ubuntu): sudo apt install python3.11 python3.11-venv"; \
		exit 1; \
	fi
	@echo "✓ 사용할 Python: $(VENV_PYTHON)"
	$(VENV_PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt
	@$(MAKE) _install-hooks
	@echo ""
	@echo "========================================"
	@echo " ✅ venv 환경 설정 완료!"
	@echo " 활성화: source $(VENV_DIR)/bin/activate"
	@echo "========================================"

_install-hooks:
	@mkdir -p .git/hooks
	@cp hooks/pre-push .git/hooks/pre-push
	@chmod +x .git/hooks/pre-push

init-update: ## 환경 업데이트 (현재 활성 환경 기준)
ifeq ($(ENV_NAME),venv)
	$(VENV_DIR)/bin/pip install -r requirements.txt --upgrade
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
	rm -rf $(VENV_DIR)
else
	conda env remove -n $(CONDA_ENV)
endif

help: ## 도움말 출력
	@echo "현재 활성 환경: $(ENV_NAME)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
