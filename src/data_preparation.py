"""
데이터 수집 및 정제 모듈
- TDC (Therapeutics Data Commons)에서 DILI 데이터셋 다운로드
- 기본 정제 (중복 제거, SMILES 유효성 검증)
"""

import os

import pandas as pd
from rdkit import Chem, RDLogger

# RDKit 경고 메시지 억제
RDLogger.logger().setLevel(RDLogger.ERROR)

# 프로젝트 루트 경로
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")


def download_tdc_dili():
    """TDC에서 DILI 데이터셋을 다운로드하고 raw 폴더에 저장."""
    from tdc.single_pred import Tox

    print("TDC DILI 데이터셋 다운로드 중...")
    data = Tox(name="DILI")
    df = data.get_data()

    os.makedirs(RAW_DIR, exist_ok=True)
    raw_path = os.path.join(RAW_DIR, "tdc_dili_raw.csv")
    df.to_csv(raw_path, index=False)
    print(f"저장 완료: {raw_path}")
    print(f"  - 샘플 수: {len(df)}")
    print(f"  - 컬럼: {list(df.columns)}")
    print(f"  - 라벨 분포:\n{df['Y'].value_counts()}")
    return df


def validate_smiles(smiles):
    """SMILES 문자열의 유효성을 검증."""
    if not isinstance(smiles, str) or len(smiles.strip()) == 0:
        return False
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None


def clean_data(df):
    """데이터 정제: 유효성 검증, 중복 제거."""
    print(f"\n데이터 정제 시작 (원본: {len(df)}개)")

    # 컬럼명 표준화 - TDC는 Drug, Drug_ID, Y 컬럼을 사용
    col_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in ("drug", "smiles"):
            col_map[col] = "SMILES"
        elif col_lower in ("y", "label"):
            col_map[col] = "Label"
        elif col_lower in ("drug_id", "name", "drug_name"):
            col_map[col] = "Name"
    df = df.rename(columns=col_map)

    # SMILES 유효성 검증
    valid_mask = df["SMILES"].apply(validate_smiles)
    n_invalid = (~valid_mask).sum()
    if n_invalid > 0:
        print(f"  - 유효하지 않은 SMILES 제거: {n_invalid}개")
    df = df[valid_mask].copy()

    # Canonical SMILES로 변환 (중복 탐지를 위해)
    df["SMILES"] = df["SMILES"].apply(lambda s: Chem.MolToSmiles(Chem.MolFromSmiles(s)))

    # 중복 SMILES 제거
    n_before = len(df)
    df = df.drop_duplicates(subset="SMILES", keep="first")
    n_dup = n_before - len(df)
    if n_dup > 0:
        print(f"  - 중복 SMILES 제거: {n_dup}개")

    # Label을 정수로 변환
    df["Label"] = df["Label"].astype(int)

    df = df.reset_index(drop=True)
    print(f"  - 최종 샘플 수: {len(df)}")
    print(f"  - 라벨 분포: 독성(1)={df['Label'].sum()}, 비독성(0)={(df['Label'] == 0).sum()}")

    return df


def prepare_dataset():
    """전체 데이터 준비 파이프라인 실행."""
    # TDC 데이터 다운로드
    raw_path = os.path.join(RAW_DIR, "tdc_dili_raw.csv")
    if os.path.exists(raw_path):
        print(f"기존 데이터 사용: {raw_path}")
        df = pd.read_csv(raw_path)
    else:
        df = download_tdc_dili()

    # 정제
    df_clean = clean_data(df)

    # 저장
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    processed_path = os.path.join(PROCESSED_DIR, "dili_dataset.csv")
    df_clean.to_csv(processed_path, index=False)
    print(f"\n정제된 데이터 저장: {processed_path}")

    return df_clean


if __name__ == "__main__":
    df = prepare_dataset()
    print("\n=== 데이터 미리보기 ===")
    print(df.head())
    print(f"\nShape: {df.shape}")
