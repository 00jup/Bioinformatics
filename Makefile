CONDA_ENV := bioinfo
CONDA_RUN := conda run -n $(CONDA_ENV)

.PHONY: init format lint check data features train predict clean help

## ──────────────────────────────────────────────
## 환경 설정
## ──────────────────────────────────────────────

init: ## conda 환경 생성 및 패키지 설치
	conda env create -f environment.yml
	@mkdir -p .git/hooks
	@cp hooks/pre-push .git/hooks/pre-push
	@chmod +x .git/hooks/pre-push
	@echo ""
	@echo "========================================"
	@echo " 환경 설정 완료!"
	@echo " 활성화: conda activate $(CONDA_ENV)"
	@echo "========================================"

init-update: ## 환경 업데이트 (environment.yml 변경 시)
	conda env update -n $(CONDA_ENV) -f environment.yml --prune

## ──────────────────────────────────────────────
## 코드 품질
## ──────────────────────────────────────────────

format: ## ruff로 코드 포맷팅
	$(CONDA_RUN) ruff format src/ notebooks/

lint: ## ruff로 린트 검사
	$(CONDA_RUN) ruff check src/

check: lint ## 포맷 + 린트 검사 (pre-push에서 사용)
	$(CONDA_RUN) ruff format --check src/

## ──────────────────────────────────────────────
## 파이프라인
## ──────────────────────────────────────────────

data: ## 데이터 다운로드 및 정제
	$(CONDA_RUN) python src/data_preparation.py

features: ## Feature 추출
	$(CONDA_RUN) python src/feature_engineering.py

train: ## 모델 학습 및 평가
	$(CONDA_RUN) python src/model_training.py

predict: ## 예측 실행 (usage: make predict INPUT=test.txt OUTPUT=result.txt)
	$(CONDA_RUN) python src/predict.py $(INPUT) -o $(OUTPUT)

all: data features train ## 전체 파이프라인 실행

## ──────────────────────────────────────────────
## 유틸리티
## ──────────────────────────────────────────────

clean: ## 생성된 파일 정리
	rm -rf data/raw/ data/processed/ models/*.pkl results/figures/*.png
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

clean-env: ## conda 환경 삭제
	conda env remove -n $(CONDA_ENV)

help: ## 도움말 출력
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
