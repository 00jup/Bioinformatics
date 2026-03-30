"""
DILI 예측 스크립트 (SHAP 설명 포함)
- SMILES를 직접 입력하면 독성 예측 + 이유를 출력
- 파일 입력도 지원

사용법:
    python src/predict.py "CCO" "CC(=O)Oc1ccccc1C(=O)O"
    python src/predict.py -f input.csv -o output.txt
"""

import argparse
import os
import sys
import warnings

import joblib
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger

RDLogger.logger().setLevel(RDLogger.ERROR)
warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.feature_engineering import extract_features  # noqa: E402

# 사람이 읽을 수 있는 descriptor 설명
DESCRIPTOR_INFO = {
    "MolWt": ("분자량", "Da", "높을수록 간 대사 부담 증가"),
    "MolLogP": ("지용성 (LogP)", "", "높으면 간 축적 위험 증가"),
    "TPSA": ("극성 표면적", "Å²", "낮으면 막 투과성 높아 간 노출 증가"),
    "NumHDonors": ("수소결합 공여체 수", "개", "약물 대사 경로에 영향"),
    "NumHAcceptors": ("수소결합 수용체 수", "개", "약물 용해성/대사에 영향"),
    "NumRotatableBonds": ("회전 가능 결합 수", "개", "분자 유연성 지표"),
    "NumAromaticRings": ("방향족 고리 수", "개", "반응성 대사체 생성 가능성"),
    "FractionCSP3": ("sp3 탄소 비율", "", "높을수록 3D 복잡성 증가"),
    "HeavyAtomCount": ("무거운 원자 수", "개", "분자 크기 지표"),
    "RingCount": ("고리 수", "개", "구조적 복잡성 지표"),
}


def load_model(model_path=None):
    """저장된 모델 로드."""
    if model_path is None:
        model_path = os.path.join(PROJECT_ROOT, "models", "best_model.pkl")
    if not os.path.exists(model_path):
        print(f"오류: 모델 파일이 없습니다: {model_path}")
        print("먼저 model_training.py를 실행하세요.")
        sys.exit(1)
    model = joblib.load(model_path)
    return model


def read_smiles_from_file(input_path, column=None):
    """파일에서 SMILES 추출."""
    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".sdf":
        suppl = Chem.SDMolSupplier(input_path)
        return [Chem.MolToSmiles(mol) if mol else None for mol in suppl]

    elif ext == ".csv":
        df = pd.read_csv(input_path)
        for col in ([column] if column else []) + ["SMILES", "smiles", "Drug"]:
            if col and col in df.columns:
                return df[col].tolist()
        return df.iloc[:, 0].tolist()

    else:
        with open(input_path, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        return [line.split("\t")[0].split(",")[0] for line in lines]


def explain_with_shap(model, feature_df, feature_names):
    """SHAP으로 각 샘플의 예측 이유를 계산."""
    import shap

    # 모델에서 tree-based estimator 추출
    explanations = []
    tree_model = None
    scaler = None

    if hasattr(model, "estimators_"):
        # VotingClassifier — estimators_는 fitted Pipeline 리스트
        for est in model.estimators_:
            if hasattr(est, "named_steps"):
                clf = est.named_steps["clf"]
                sc = est.named_steps.get("scaler")
                if hasattr(clf, "feature_importances_"):
                    tree_model = clf
                    scaler = sc
                    break
    elif hasattr(model, "named_steps"):
        # 단일 Pipeline
        tree_model = model.named_steps["clf"]
        scaler = model.named_steps.get("scaler")

    if tree_model is None:
        return None

    # 스케일링된 데이터로 SHAP 계산
    X = feature_df.values
    if scaler is not None:
        X_scaled = scaler.transform(X)
    else:
        X_scaled = X

    explainer = shap.TreeExplainer(tree_model)
    shap_values = explainer.shap_values(X_scaled)

    # binary classification: 독성(1) 클래스의 SHAP values
    if isinstance(shap_values, list):
        shap_vals = shap_values[1]  # class 1 (toxic)
    elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
        shap_vals = shap_values[:, :, 1]  # (samples, features, classes) -> class 1
    else:
        shap_vals = shap_values

    for i in range(len(feature_df)):
        sample_shap = shap_vals[i]
        # SHAP 절대값 기준 상위 feature 선택
        top_indices = np.argsort(np.abs(sample_shap))[::-1]

        reasons = []
        for idx in top_indices:
            idx = int(idx)
            name = feature_names[idx]
            shap_val = float(sample_shap[idx])
            raw_val = feature_df.iloc[i, idx]

            # descriptor인 경우 사람이 읽을 수 있게
            if name in DESCRIPTOR_INFO:
                desc_name, unit, desc = DESCRIPTOR_INFO[name]
                unit_str = f" {unit}" if unit else ""
                direction = "독성 증가" if shap_val > 0 else "독성 감소"
                reasons.append(
                    {
                        "feature": name,
                        "display_name": desc_name,
                        "value": raw_val,
                        "unit": unit_str,
                        "shap": shap_val,
                        "direction": direction,
                        "description": desc,
                    }
                )
            elif name.startswith("Morgan_") and raw_val == 1:
                # 활성화된 fingerprint bit만 표시
                direction = "독성 증가" if shap_val > 0 else "독성 감소"
                reasons.append(
                    {
                        "feature": name,
                        "display_name": f"구조 특성 ({name})",
                        "value": int(raw_val),
                        "unit": "",
                        "shap": shap_val,
                        "direction": direction,
                        "description": "분자 내 특정 하위구조 존재",
                    }
                )

            if len(reasons) >= 5:
                break

        explanations.append(reasons)

    return explanations


def predict_and_explain(smiles_list, model, feature_set="B"):
    """SMILES 리스트에 대해 예측 + 설명 수행."""
    # Feature 추출
    feature_df, valid_indices = extract_features(smiles_list, feature_set=feature_set)
    feature_names = feature_df.columns.tolist()

    X = feature_df.values
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]

    # SHAP 설명
    explanations = explain_with_shap(model, feature_df, feature_names)

    # 결과 조합
    results = []
    valid_set = set(valid_indices)

    for i, smi in enumerate(smiles_list):
        if i not in valid_set:
            results.append(
                {
                    "smiles": smi,
                    "prediction": -1,
                    "probability": None,
                    "label": "변환 실패",
                    "reasons": [],
                }
            )
            continue

        vi = valid_indices.index(i)
        pred = int(predictions[vi])
        prob = float(probabilities[vi])

        results.append(
            {
                "smiles": smi,
                "prediction": pred,
                "probability": prob,
                "label": "독성 (DILI)" if pred == 1 else "비독성",
                "reasons": explanations[vi] if explanations else [],
            }
        )

    return results


def format_result(result, index=None):
    """결과를 보기 좋게 포맷팅."""
    lines = []
    prefix = f"[{index}] " if index is not None else ""

    if result["prediction"] == -1:
        lines.append(f"{prefix}SMILES: {result['smiles']}")
        lines.append("  -> 유효하지 않은 SMILES (변환 실패)")
        return "\n".join(lines)

    prob = result["probability"]
    label = result["label"]

    lines.append(f"{prefix}SMILES: {result['smiles']}")
    lines.append(f"  예측: {label} (독성 확률: {prob:.1%})")

    if result["reasons"]:
        lines.append("  근거:")
        for r in result["reasons"]:
            arrow = "+" if r["shap"] > 0 else "-"
            if r["feature"] in DESCRIPTOR_INFO:
                val_str = f"{r['value']:.2f}" if isinstance(r["value"], float) else str(r["value"])
                lines.append(
                    f"    [{arrow}] {r['display_name']} = {val_str}{r['unit']} "
                    f"({r['direction']}) — {r['description']}"
                )
            else:
                lines.append(f"    [{arrow}] {r['display_name']} ({r['direction']})")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="DILI 독성 예측 — SMILES 입력 → 예측 + 이유",
        usage="%(prog)s SMILES [SMILES ...]\n       %(prog)s -f input_file [-o output.txt]",
    )
    parser.add_argument("smiles", nargs="*", help="예측할 SMILES 문자열 (여러 개 가능)")
    parser.add_argument("-f", "--file", default=None, help="SMILES가 담긴 입력 파일")
    parser.add_argument("-o", "--output", default=None, help="결과 저장 파일")
    parser.add_argument("--model", default=None, help="모델 파일 경로")
    parser.add_argument("--column", default=None, help="CSV의 SMILES 컬럼명")
    parser.add_argument("--feature-set", default="B", help="Feature set (A/B/C/D)")
    args = parser.parse_args()

    # SMILES 수집
    smiles_list = []
    if args.smiles:
        smiles_list = args.smiles
    elif args.file:
        smiles_list = read_smiles_from_file(args.file, column=args.column)
    else:
        parser.print_help()
        print("\nSMILES를 직접 입력하거나 -f 옵션으로 파일을 지정하세요.")
        sys.exit(1)

    # 유효성 체크
    smiles_list = [s for s in smiles_list if s and str(s).strip()]
    if not smiles_list:
        print("오류: 입력된 SMILES가 없습니다.")
        sys.exit(1)

    # 모델 로드
    model = load_model(args.model)

    # 예측 + 설명
    results = predict_and_explain(smiles_list, model, args.feature_set)

    # 출력
    print(f"\n{'=' * 60}")
    print(f"  DILI 독성 예측 결과 ({len(results)}개)")
    print(f"{'=' * 60}")

    output_lines = []
    for i, result in enumerate(results, 1):
        text = format_result(result, index=i)
        print(f"\n{text}")
        output_lines.append(text)

    # 요약
    n_toxic = sum(1 for r in results if r["prediction"] == 1)
    n_safe = sum(1 for r in results if r["prediction"] == 0)
    n_fail = sum(1 for r in results if r["prediction"] == -1)
    print(f"\n{'=' * 60}")
    print(f"  요약: 독성 {n_toxic}개 / 비독성 {n_safe}개", end="")
    if n_fail:
        print(f" / 실패 {n_fail}개", end="")
    print(f"\n{'=' * 60}")

    # 파일 저장
    if args.output:
        with open(args.output, "w") as f:
            f.write("\n\n".join(output_lines) + "\n")
        print(f"\n결과 저장: {args.output}")


if __name__ == "__main__":
    main()
