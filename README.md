# DILI Prediction Pipeline

약물의 화학 구조(SMILES)를 입력하면 간독성(Drug-Induced Liver Injury) 여부를 예측하고, SHAP 기반으로 예측 근거를 설명합니다.

## Pipeline

```
SMILES 입력
  → RDKit으로 분자 변환
  → Feature 추출 (Morgan FP 2048 + Physicochemical Descriptors 10)
  → ML Ensemble (RF + LightGBM + XGBoost)
  → 독성/비독성 예측 + SHAP 근거 설명
```

## 설치

지원 Python: 3.10 / 3.11 / 3.12 / 3.13

```bash
make init-venv          # venv 자동 생성 (3.10~3.13 자동 감지)
source .venv/bin/activate

# 또는 conda
make init-conda
conda activate bioinfo
```

> 💡 데이터 새로 받거나 (TDC), 개발 (lint/test) 하려면:
> ```bash
> pip install -r requirements-dev.txt
> ```
> PyTDC가 옛 sklearn 핀을 강제해서 일반 의존성에서 분리. 평소엔 깔 필요 없음.

## 사용법

### SMILES로 바로 예측

```bash
python src/predict.py "CC(=O)Oc1ccccc1C(=O)O" "CC(=O)Nc1ccc(O)cc1"
```

```
[1] (Aspirin)
  SMILES: CC(=O)Oc1ccccc1C(=O)O
  예측: 비독성 (독성 확률: 7.7%)
  근거:
    [-] 고리 수 = 1.00 개 (독성 감소) — 구조적 복잡성 지표
    [-] 방향족 고리 수 = 1.00 개 (독성 감소) — 반응성 대사체 생성 가능성
    [-] 분자량 = 180.16 Da (독성 감소) — 높을수록 간 대사 부담 증가
```

### 파일 입력

```bash
# CSV (Name, SMILES 컬럼 자동 탐지)
python src/predict.py -f data/sample_input.csv

# 샘플 데이터로 빠른 데모
make predict-sample
```

### 평가셋 100개 한 번에 예측 (CSV 결과)

교수님이 주신 평가용 데이터(SMILES 100개 등)를 한 번에 예측하고 CSV로 저장합니다.

```bash
# 1) 평가 데이터를 data/test/professor_test.csv 로 저장 (컬럼: Name,SMILES)
# 2) 실행
make predict-test
```

- 콘솔: 항목별 예측 + `독성 N개 / 비독성 N개` 요약
- CSV: `results/predictions_professor_test.csv`
  (컬럼: `Name, SMILES, prediction(0/1/-1), label, probability, top_reasons`)
- 입력 N개 = 출력 N행. SMILES 변환 실패 행은 `prediction=-1`로 기록됩니다.
- 파일명이 다르면: `make predict-test FILE=data/test/다른이름.csv`

## 워크플로우

```
make data       → 데이터 다운로드 + train/validation/test 분할
make features   → Feature 추출
make train      → Train set으로 학습 + Validation 평가
                  ↓
          Validation 결과 확인 (models/validation_results.json)
          → 성능이 낮으면? 하이퍼파라미터 수정 후 make train 재실행
          → make validate 로 재평가
                  ↓
          만족하면?
make test       → Test set으로 최종 평가 (1번만 실행)
```

## 데이터

- 출처: [Therapeutics Data Commons (TDC)](https://tdcommons.ai/) DILI 데이터셋
- `make data`로 자동 다운로드, 정제, 분할

```
data/
  raw/           ← 원본 데이터 (TDC 다운로드)
  processed/     ← 정제된 전체 데이터
  train/         ← 학습용 331개 (70%)
  validation/    ← 모델 조절용 72개 (15%)
  test/          ← 최종 평가용 72개 (15%)
```

## 모델 성능

Train set 10-fold Stratified CV:

| Model | AUC | Accuracy | F1 | Precision | Recall |
|-------|-----|----------|-----|-----------|--------|
| **Random Forest** | **0.915** | 0.852 | 0.849 | 0.860 | 0.841 |
| XGBoost | 0.895 | 0.840 | 0.836 | 0.848 | 0.829 |
| LightGBM | 0.892 | 0.822 | 0.820 | 0.821 | 0.823 |
| SVM (RBF) | 0.827 | 0.743 | 0.760 | 0.714 | 0.816 |
| Neural Network | 0.826 | 0.749 | 0.758 | 0.737 | 0.787 |

Validation set 평가: AUC 0.891, F1 0.827

최종 모델: RF + XGBoost + LightGBM Soft Voting 앙상블

## Feature Set

| Set | 구성 | 차원 |
|-----|------|------|
| A | Morgan FP (ECFP4) | 2048 |
| **B (기본)** | **Morgan FP + Physicochemical Descriptors** | **2058** |
| C | Morgan FP + MACCS Keys + Descriptors | ~2225 |
| D | Physicochemical Descriptors only | 10 |

## 프로젝트 구조

```
src/
  data_preparation.py      # 데이터 다운로드, 정제, train/val/test 분할
  feature_engineering.py   # Morgan FP + Descriptor 추출
  model_training.py        # 5개 모델 10-fold CV + 앙상블 + Validation 평가
  predict.py               # SMILES 입력 → 예측 + SHAP 설명
notebooks/
  01_eda.ipynb             # 탐색적 데이터 분석
  02_model_comparison.ipynb # 모델 비교
models/
  best_model.pkl           # 학습된 앙상블 모델
  cv_results.json          # CV 결과
  validation_results.json  # Validation 평가 결과
  model_meta.json          # 모델 메타데이터
data/
  sample_input.csv         # 예측용 샘플 입력 파일
  test/professor_test.csv  # 평가셋 입력 (make predict-test)
results/
  figures/                 # ROC curve, Confusion matrix
  predictions_*.csv         # make predict-test 예측 결과
```

## Make 명령어

| 명령어 | 설명 |
|--------|------|
| `make init` | conda 환경 생성 |
| `make all` | 전체 파이프라인 (data → features → train) |
| `make data` | 데이터 다운로드 + train/validation/test 분할 |
| `make features` | Feature 추출 |
| `make train` | Train set 학습 + Validation 평가 |
| `make validate` | Validation set 재평가 (파라미터 수정 후 확인용) |
| `make test` | Test set 최종 평가 (마지막에 1번만) |
| `make predict` | 예측 (`make predict INPUT=data/sample_input.csv`) |
| `make predict-sample` | 샘플 데이터로 빠른 예측 데모 |
| `make predict-test` | 평가셋 100개 예측 → `results/` CSV 저장 |
| `make format` | ruff 코드 포맷팅 |
| `make lint` | ruff 린트 검사 |
| `make check` | 포맷 + 린트 검사 |
| `make clean` | 생성 파일 정리 |
| `make clean-env` | 가상환경 삭제 |
