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

```bash
# conda 환경 생성
make init
conda activate bioinfo
```

## 사용법

### SMILES로 바로 예측

```bash
python src/predict.py "CC(=O)Oc1ccccc1C(=O)O" "CC(=O)Nc1ccc(O)cc1"
```

```
[1] SMILES: CC(=O)Oc1ccccc1C(=O)O
  예측: 비독성 (독성 확률: 7.7%)
  근거:
    [-] 고리 수 = 1.00 개 (독성 감소) — 구조적 복잡성 지표
    [-] 방향족 고리 수 = 1.00 개 (독성 감소) — 반응성 대사체 생성 가능성
    [-] 분자량 = 180.16 Da (독성 감소) — 높을수록 간 대사 부담 증가

[2] SMILES: CC(=O)Nc1ccc(O)cc1
  예측: 비독성 (독성 확률: 13.0%)
  근거:
    [-] 분자량 = 151.16 Da (독성 감소) — 높을수록 간 대사 부담 증가
    [-] 방향족 고리 수 = 1.00 개 (독성 감소) — 반응성 대사체 생성 가능성
```

### 파일 입력

```bash
# CSV (SMILES 컬럼 자동 탐지)
python src/predict.py -f input.csv -o result.txt

# 텍스트 (한 줄에 SMILES 하나)
python src/predict.py -f input.txt -o result.txt
```

### 전체 파이프라인 재실행 (데이터 수집 → 학습 → 평가)

```bash
make all
```

## 모델 성능

10-fold Stratified Cross Validation:

| Model | AUC | Accuracy | F1 | Precision | Recall |
|-------|-----|----------|-----|-----------|--------|
| **Random Forest** | **0.908** | 0.826 | 0.822 | 0.841 | 0.815 |
| LightGBM | 0.893 | 0.796 | 0.796 | 0.790 | 0.809 |
| XGBoost | 0.892 | 0.815 | 0.816 | 0.818 | 0.818 |
| SVM (RBF) | 0.846 | 0.760 | 0.781 | 0.718 | 0.861 |
| Neural Network | 0.822 | 0.752 | 0.763 | 0.733 | 0.801 |

최종 모델: 상위 3개(RF + LightGBM + XGBoost)의 Soft Voting 앙상블

## 데이터

- 출처: [Therapeutics Data Commons (TDC)](https://tdcommons.ai/) DILI 데이터셋
- `make data`로 자동 다운로드 및 정제 (중복 제거, SMILES 유효성 검증)

## Feature Set

| Set | 구성 | 차원 |
|-----|------|------|
| A | Morgan FP (ECFP4) | 2048 |
| **B (기본)** | **Morgan FP + Physicochemical Descriptors** | **2058** |
| C | Morgan FP + MACCS Keys + Descriptors | ~2225 |
| D | Physicochemical Descriptors only | 10 |

Physicochemical Descriptors: MolWt, LogP, TPSA, H-bond donors/acceptors, Rotatable bonds, Aromatic rings, FractionCSP3, Heavy atom count, Ring count

## 프로젝트 구조

```
src/
  data_preparation.py      # TDC 데이터 다운로드 및 정제
  feature_engineering.py   # Morgan FP + Descriptor 추출
  model_training.py        # 5개 모델 10-fold CV + 앙상블
  predict.py               # SMILES 입력 → 예측 + SHAP 설명
notebooks/
  01_eda.ipynb             # 탐색적 데이터 분석
  02_model_comparison.ipynb # 모델 비교
models/
  best_model.pkl           # 학습된 앙상블 모델
  cv_results.json          # CV 결과
  model_meta.json          # 모델 메타데이터
data/                      # raw + processed 데이터
results/figures/           # ROC curve, Confusion matrix
```

## Make 명령어

| 명령어 | 설명 |
|--------|------|
| `make init` | conda 환경 생성 |
| `make all` | 전체 파이프라인 (data → features → train) |
| `make data` | 데이터 다운로드/정제 |
| `make features` | Feature 추출 |
| `make train` | 모델 학습/평가 |
| `make format` | ruff 코드 포맷팅 |
| `make lint` | ruff 린트 검사 |
| `make clean` | 생성 파일 정리 |
