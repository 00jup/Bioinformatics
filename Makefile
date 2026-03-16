PYTHON := python3.10
VENV := .venv
BIN := $(VENV)/bin

.PHONY: init format lint check data features train predict clean help

## ──────────────────────────────────────────────
## 환경 설정
## ──────────────────────────────────────────────

init: ## venv 생성, 패키지 설치, pre-push hook 설정
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	$(BIN)/pip install ruff
	@mkdir -p .git/hooks
	@cp hooks/pre-push .git/hooks/pre-push
	@chmod +x .git/hooks/pre-push
	@echo ""
	@echo "========================================"
	@echo " 환경 설정 완료!"
	@echo " 활성화: source $(VENV)/bin/activate"
	@echo "========================================"

## ──────────────────────────────────────────────
## 코드 품질
## ──────────────────────────────────────────────

format: ## ruff로 코드 포맷팅
	$(BIN)/ruff format src/ notebooks/

lint: ## ruff로 린트 검사
	$(BIN)/ruff check src/

check: lint ## 포맷 + 린트 검사 (pre-push에서 사용)
	$(BIN)/ruff format --check src/

## ──────────────────────────────────────────────
## 파이프라인
## ──────────────────────────────────────────────

data: ## 데이터 다운로드 및 정제
	$(BIN)/python src/data_preparation.py

features: ## Feature 추출
	$(BIN)/python src/feature_engineering.py

train: ## 모델 학습 및 평가
	$(BIN)/python src/model_training.py

predict: ## 예측 실행 (usage: make predict INPUT=test.txt OUTPUT=result.txt)
	$(BIN)/python src/predict.py $(INPUT) -o $(OUTPUT)

all: data features train ## 전체 파이프라인 실행

## ──────────────────────────────────────────────
## 유틸리티
## ──────────────────────────────────────────────

clean: ## 생성된 파일 정리 (venv 제외)
	rm -rf data/raw/ data/processed/ models/*.pkl results/figures/*.png
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

help: ## 도움말 출력
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
