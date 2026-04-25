"""End-to-end mock 파이프라인 테스트."""

from unittest.mock import patch

import pandas as pd


def _mock_chembl():
    return pd.DataFrame(
        [
            {
                "chembl_id": "CHEMBL25",
                "pref_name": "ASPIRIN",
                "name": "ASPIRIN",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "max_phase": 4,
                "withdrawn_flag": False,
            },
            {
                "chembl_id": "CHEMBL112",
                "pref_name": "PARACETAMOL",
                "name": "PARACETAMOL",
                "smiles": "CC(=O)Nc1ccc(O)cc1",
                "max_phase": 4,
                "withdrawn_flag": False,
            },
            {
                "chembl_id": "CHEMBL1431",
                "pref_name": "METFORMIN",
                "name": "METFORMIN",
                "smiles": "CN(C)C(=N)N=C(N)N",
                "max_phase": 4,
                "withdrawn_flag": False,
            },
            {
                "chembl_id": "CHEMBL113",
                "pref_name": "CAFFEINE",
                "name": "CAFFEINE",
                "smiles": "Cn1cnc2c1c(=O)n(C)c(=O)n2C",
                "max_phase": 4,
                "withdrawn_flag": False,
            },
        ]
    )


def _mock_drugcentral():
    return pd.DataFrame(
        [
            {
                "drugcentral_id": "1",
                "name": "aspirin",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "inchi_key": "",
            }
        ]
    )


def _mock_pubchem():
    return pd.DataFrame(
        [
            {
                "cid": "2244",
                "name": "Aspirin",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "inchi_key": "",
            }
        ]
    )


def _mock_inxight():
    return pd.DataFrame(
        [
            {
                "unii": "R16CO5Y76E",
                "name": "Aspirin",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "inchi_key": "",
                "marketing_status": "Marketed",
            }
        ]
    )


def _mock_kegg():
    return pd.DataFrame(
        [
            {
                "kegg_id": "D00109",
                "name": "Aspirin",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "inchi_key": "",
                "atc_code": "N02BA01",
            }
        ]
    )


def _mock_drugbank():
    return pd.DataFrame(
        [
            {
                "drugbank_id": "DB00945",
                "name": "Aspirin",
                "smiles": "",
                "inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                "unii": "R16CO5Y76E",
            }
        ]
    )


def test_full_pipeline_mock(tmp_path, monkeypatch):
    import src.marketed_drugs.__main__ as main_mod

    monkeypatch.setattr(main_mod, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(main_mod, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(main_mod, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(main_mod, "REFERENCE_DIR", tmp_path / "reference")
    monkeypatch.setattr(
        main_mod,
        "SOURCES",
        {
            "chembl": _mock_chembl,
            "drugcentral": _mock_drugcentral,
            "pubchem": _mock_pubchem,
            "inxight": _mock_inxight,
            "kegg": _mock_kegg,
            "drugbank": _mock_drugbank,
        },
    )

    rc = main_mod.run_pipeline()
    assert rc == 0

    all_csv = pd.read_csv(tmp_path / "all" / "marketed_all.csv")
    clean_csv = pd.read_csv(tmp_path / "non_hepatotoxic" / "marketed_clean.csv")
    assert len(all_csv) >= 1
    assert "canonical_smiles" in all_csv.columns
    assert "known_hepatotoxic" in all_csv.columns
    assert (clean_csv["known_hepatotoxic"] == 0).all()
