# Bioinformatics - DILI Prediction

Drug-Induced Liver Injury (DILI) 예측을 위한 머신러닝 파이프라인

## Overview

약물의 화학 구조(SMILES)로부터 간독성 여부를 예측하는 Binary Classification 모델

## Pipeline

```
SMILES → Morgan FP (2048) + MACCS (167) + Descriptors (~10) → ML Models → 0/1 (독성/비독성)
```

## Models

| Model | AUC (10-fold CV) |
|-------|-----------------|
| Random Forest | **0.908** |
| LightGBM | 0.893 |
| XGBoost | 0.892 |
| SVM (RBF) | 0.846 |
| Neural Network | 0.822 |

Final: RF + LightGBM + XGBoost Ensemble (Soft Voting)

## Quick Start

```bash
pip install -r requirements.txt
make all        # 전체 파이프라인 실행
```

## Project Structure

```
├── src/
│   ├── data_preparation.py      # 데이터 수집/정제
│   ├── feature_engineering.py   # 분자 특성 추출
│   ├── model_training.py        # 모델 학습/평가
│   └── predict.py               # 예측 스크립트
├── notebooks/
│   ├── 01_eda.ipynb             # 탐색적 데이터 분석
│   └── 02_model_comparison.ipynb # 모델 비교
├── models/                       # 저장된 모델
├── data/                         # 데이터셋
└── results/figures/              # 시각화 결과
```
