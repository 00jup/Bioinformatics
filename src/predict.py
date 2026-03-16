"""
시험 당일 예측 스크립트
- 다양한 입력 형식 지원 (SMILES, 약물명, SDF)
- 저장된 모델로 빠르게 예측
- 결과를 TEXT FILE로 출력 (헤더 없음, 순서 유지, 0/1만 포함)

사용법:
    python src/predict.py input_file.txt -o output.txt
    python src/predict.py input_file.csv -o output.txt --column SMILES
    python src/predict.py input_file.sdf -o output.txt
"""

import argparse
import os
import sys
import time

import joblib
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger

RDLogger.logger().setLevel(RDLogger.ERROR)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.feature_engineering import extract_features  # noqa: E402


def load_model(model_path=None):
    """저장된 모델 로드."""
    if model_path is None:
        model_path = os.path.join(PROJECT_ROOT, "models", "best_model.pkl")
    if not os.path.exists(model_path):
        print(f"오류: 모델 파일이 없습니다: {model_path}")
        print("먼저 model_training.py를 실행하세요.")
        sys.exit(1)
    model = joblib.load(model_path)
    print(f"모델 로드 완료: {model_path}")
    return model


def read_input(input_path, column=None):
    """다양한 형식의 입력 파일에서 SMILES 추출."""
    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".sdf":
        # SDF 파일
        suppl = Chem.SDMolSupplier(input_path)
        smiles_list = []
        for mol in suppl:
            if mol is not None:
                smiles_list.append(Chem.MolToSmiles(mol))
            else:
                smiles_list.append(None)
        print(f"SDF에서 {len(smiles_list)}개 분자 로드")
        return smiles_list

    elif ext == ".csv":
        # CSV 파일
        df = pd.read_csv(input_path)
        if column and column in df.columns:
            smiles_list = df[column].tolist()
        elif "SMILES" in df.columns:
            smiles_list = df["SMILES"].tolist()
        elif "smiles" in df.columns:
            smiles_list = df["smiles"].tolist()
        elif "Drug" in df.columns:
            smiles_list = df["Drug"].tolist()
        else:
            # 첫 번째 컬럼이 SMILES라고 가정
            smiles_list = df.iloc[:, 0].tolist()
        print(f"CSV에서 {len(smiles_list)}개 SMILES 로드")
        return smiles_list

    else:
        # TXT 또는 기타 - 한 줄에 하나의 SMILES/약물명
        with open(input_path, "r") as f:
            lines = [line.strip() for line in f if line.strip()]

        # 탭/콤마로 구분된 경우 첫 번째 필드 사용
        smiles_list = []
        for line in lines:
            if "\t" in line:
                smiles_list.append(line.split("\t")[0])
            elif "," in line:
                # SMILES 안에 쉼표가 없으므로 안전
                smiles_list.append(line.split(",")[0])
            else:
                smiles_list.append(line)

        print(f"텍스트에서 {len(smiles_list)}개 항목 로드")
        return smiles_list


def resolve_names_to_smiles(items):
    """약물명인 경우 PubChemPy로 SMILES 변환 시도."""
    resolved = []
    needs_lookup = []

    for i, item in enumerate(items):
        if item is None:
            resolved.append(None)
            continue
        mol = Chem.MolFromSmiles(item)
        if mol is not None:
            # 이미 유효한 SMILES
            resolved.append(item)
        else:
            # SMILES가 아님 → 약물명으로 간주
            needs_lookup.append((i, item))
            resolved.append(None)

    if needs_lookup:
        print(f"약물명 {len(needs_lookup)}개 → SMILES 변환 시도 중...")
        try:
            import pubchempy as pcp

            for idx, name in needs_lookup:
                try:
                    compounds = pcp.get_compounds(name, "name")
                    if compounds:
                        resolved[idx] = compounds[0].isomeric_smiles
                    else:
                        print(f"  경고: '{name}' → SMILES 변환 실패")
                except Exception as e:
                    print(f"  경고: '{name}' 조회 오류: {e}")
        except ImportError:
            print("  pubchempy 미설치. 약물명 변환 불가.")
            print("  pip install pubchempy 후 재시도하세요.")

    return resolved


def predict(smiles_list, model, feature_set="B"):
    """SMILES 리스트에 대해 예측 수행."""
    # Feature 추출
    feature_df, valid_indices = extract_features(smiles_list, feature_set=feature_set)

    # 예측
    X = feature_df.values
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]

    # 전체 결과 (유효하지 않은 SMILES는 -1로 표시)
    full_predictions = np.full(len(smiles_list), -1, dtype=int)
    full_probabilities = np.full(len(smiles_list), np.nan)

    for i, idx in enumerate(valid_indices):
        full_predictions[idx] = int(predictions[i])
        full_probabilities[idx] = probabilities[i]

    return full_predictions, full_probabilities


def save_results(predictions, output_path):
    """예측 결과를 텍스트 파일로 저장 (헤더 없음, 0/1만)."""
    with open(output_path, "w") as f:
        for pred in predictions:
            # 변환 실패(-1)인 경우 0으로 기본 출력
            f.write(f"{max(pred, 0)}\n")
    print(f"예측 결과 저장: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="DILI 예측 스크립트")
    parser.add_argument("input", help="입력 파일 경로 (SMILES/약물명/SDF)")
    parser.add_argument("-o", "--output", default="predictions.txt", help="출력 파일 경로")
    parser.add_argument("--model", default=None, help="모델 파일 경로")
    parser.add_argument("--column", default=None, help="CSV의 SMILES 컬럼명")
    parser.add_argument("--feature-set", default="B", help="Feature set (A/B/C/D)")
    parser.add_argument("--verbose", action="store_true", help="상세 출력")
    args = parser.parse_args()

    start_time = time.time()

    # 1. 모델 로드
    model = load_model(args.model)

    # 2. 입력 읽기
    items = read_input(args.input, column=args.column)

    # 3. SMILES 변환 (필요한 경우)
    smiles_list = resolve_names_to_smiles(items)

    # 유효한 SMILES 수 확인
    valid_count = sum(1 for s in smiles_list if s is not None)
    print(f"유효한 SMILES: {valid_count}/{len(smiles_list)}")

    # None → 빈 문자열로 대체 (extract_features에서 처리)
    smiles_list = [s if s is not None else "" for s in smiles_list]

    # 4. 예측
    predictions, probabilities = predict(smiles_list, model, args.feature_set)

    # 5. 결과 저장
    save_results(predictions, args.output)

    # 6. 요약
    elapsed = time.time() - start_time
    n_toxic = (predictions == 1).sum()
    n_nontoxic = (predictions == 0).sum()
    n_failed = (predictions == -1).sum()

    print("\n=== 예측 요약 ===")
    print(f"총 입력: {len(predictions)}개")
    print(f"독성(1): {n_toxic}개")
    print(f"비독성(0): {n_nontoxic}개")
    if n_failed > 0:
        print(f"실패(-1→0): {n_failed}개")
    print(f"소요 시간: {elapsed:.1f}초")

    if args.verbose:
        print("\n상세 결과:")
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            label = "독성" if pred == 1 else "비독성"
            prob_str = f"{prob:.3f}" if not np.isnan(prob) else "N/A"
            print(f"  {i + 1:3d}: {label} (확률={prob_str})")


if __name__ == "__main__":
    main()
