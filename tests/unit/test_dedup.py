import pandas as pd

from src.marketed_drugs.merge import filter_withdrawn, merge_sources


def test_merge_combines_same_canonical_smiles():
    raw = {
        "chembl": pd.DataFrame(
            [{"chembl_id": "CHEMBL25", "name": "ASPIRIN", "smiles": "CC(=O)Oc1ccccc1C(=O)O"}]
        ),
        "pubchem": pd.DataFrame(
            [{"cid": 2244, "name": "Aspirin", "smiles": "OC(=O)c1ccccc1OC(C)=O"}]
        ),
    }
    df = merge_sources(raw)
    assert len(df) == 1
    row = df.iloc[0]
    assert "chembl" in row["sources"]
    assert "pubchem" in row["sources"]
    assert "CHEMBL25" in row["source_ids"]
    assert "2244" in row["source_ids"]


def test_merge_drops_invalid_smiles():
    raw = {
        "chembl": pd.DataFrame(
            [
                {"chembl_id": "CHEMBL_BAD", "name": "BAD", "smiles": "not_a_smiles"},
                {"chembl_id": "CHEMBL25", "name": "ASPIRIN", "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
            ]
        )
    }
    df = merge_sources(raw)
    assert len(df) == 1
    assert df.iloc[0]["source_ids"] == "CHEMBL25"


def test_merge_canonical_smiles_unique_invariant():
    raw = {
        "chembl": pd.DataFrame([{"chembl_id": "A1", "name": "x", "smiles": "CCO"}]),
        "pubchem": pd.DataFrame([{"cid": "B1", "name": "y", "smiles": "OCC"}]),
    }
    df = merge_sources(raw)
    assert df["canonical_smiles"].is_unique


def test_filter_withdrawn_removes_drugbank_withdrawn():
    df = pd.DataFrame(
        [
            {
                "canonical_smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                "sources": "chembl",
                "source_ids": "CHEMBL25",
                "name": "Aspirin",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
            },
            {
                "canonical_smiles": "Cc1c(C)c2c(c(C)c1O)CCC(C)(COc1ccc(CC3SC(=O)NC3=O)cc1)O2",
                "inchi_key": "GXPHKUHSUJUWKP-UHFFFAOYSA-N",
                "sources": "chembl",
                "source_ids": "CHEMBL193",
                "name": "Troglitazone",
                "smiles": "...",
            },
        ]
    )
    drugbank_status = pd.DataFrame(
        [{"drugbank_id": "DB00197", "inchi_key": "GXPHKUHSUJUWKP-UHFFFAOYSA-N", "withdrawn": True}]
    )

    result, removed = filter_withdrawn(df, drugbank_status=drugbank_status)
    assert len(result) == 1
    assert result.iloc[0]["name"] == "Aspirin"
    assert len(removed) == 1
