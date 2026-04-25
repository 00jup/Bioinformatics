"""ChEMBL 파서 검증 (fixture 기반, 실제 API 호출 없음)."""

import json
from unittest.mock import patch

import pandas as pd

from src.marketed_drugs.chembl import collect_chembl


def test_chembl_parser_extracts_phase4_drugs(fixtures_dir):
    fixture = json.loads((fixtures_dir / "chembl_response.json").read_text())

    with patch("src.marketed_drugs.chembl.fetch_json", return_value=fixture):
        df = collect_chembl()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert set(df.columns) >= {
        "chembl_id",
        "pref_name",
        "smiles",
        "max_phase",
        "withdrawn_flag",
    }
    assert (df["max_phase"] == 4).all()
    assert "CHEMBL25" in df["chembl_id"].values

    aspirin = df[df["chembl_id"] == "CHEMBL25"].iloc[0]
    assert aspirin["smiles"] == "CC(=O)Oc1ccccc1C(=O)O"
    assert aspirin["pref_name"] == "ASPIRIN"


def test_chembl_parser_drops_rows_without_smiles():
    fixture = {
        "molecules": [
            {
                "molecule_chembl_id": "CHEMBL_NO_STRUCT",
                "pref_name": "FOO",
                "max_phase": 4,
                "withdrawn_flag": False,
                "molecule_structures": None,
            }
        ],
        "page_meta": {"next": None, "total_count": 1},
    }

    with patch("src.marketed_drugs.chembl.fetch_json", return_value=fixture):
        df = collect_chembl()

    assert len(df) == 0
