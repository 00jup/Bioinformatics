CONDA_ENV := bioinfo
CONDA_RUN := conda run -n $(CONDA_ENV)

.PHONY: init format lint check data features train validate test predict all clean help

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

data: ## 데이터 다운로드, 정제, train/validation/test 분할
	$(CONDA_RUN) python src/data_preparation.py

features: ## Feature 추출
	$(CONDA_RUN) python src/feature_engineering.py

train: ## Train set으로 모델 학습 + Validation 평가
	$(CONDA_RUN) python src/model_training.py

validate: ## Validation set으로 현재 모델 평가 (모델 조절용)
	$(CONDA_RUN) python -c "\
from src.model_training import load_split_data, evaluate_on_set, load_model_from_disk; \
import joblib; \
model = joblib.load('models/best_model.pkl'); \
X_val, y_val = load_split_data('validation', feature_set='B'); \
evaluate_on_set(model, X_val, y_val, 'Validation')"

test: ## Test set으로 최종 평가 (마지막에 1번만 실행)
	$(CONDA_RUN) python -c "\
from src.model_training import load_split_data, evaluate_on_set; \
import joblib; \
model = joblib.load('models/best_model.pkl'); \
X_test, y_test = load_split_data('test', feature_set='B'); \
evaluate_on_set(model, X_test, y_test, 'Test')"

predict: ## 예측 (usage: make predict INPUT=data/sample_input.csv)
	$(CONDA_RUN) python src/predict.py -f $(INPUT) $(if $(OUTPUT),-o $(OUTPUT)) $(if $(FORMAT),--format $(FORMAT))

all: data features train ## 전체 파이프라인 (data → features → train + validation)

## ──────────────────────────────────────────────
## 유틸리티
## ──────────────────────────────────────────────

clean: ## 생성된 파일 정리
	rm -rf data/raw/ data/processed/ data/train/ data/validation/ data/test/ models/*.pkl models/*.json results/figures/*.png
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

clean-env: ## conda 환경 삭제
	conda env remove -n $(CONDA_ENV)

help: ## 도움말 출력
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
