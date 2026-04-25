import pandas as pd

from src.marketed_drugs.merge import merge_sources


def test_merge_full_six_sources():
    """6개 소스를 모두 합쳤을 때 결과 검증."""
    raw = {
        "chembl": pd.DataFrame(
            [{"chembl_id": "CHEMBL25", "name": "ASPIRIN", "smiles": "CC(=O)Oc1ccccc1C(=O)O"}]
        ),
        "drugcentral": pd.DataFrame(
            [{"drugcentral_id": "1", "name": "aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"}]
        ),
        "pubchem": pd.DataFrame(
            [{"cid": "2244", "name": "Aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"}]
        ),
        "inxight": pd.DataFrame(
            [{"unii": "R16CO5Y76E", "name": "ASPIRIN", "smiles": "CC(=O)Oc1ccccc1C(=O)O"}]
        ),
        "kegg": pd.DataFrame(
            [{"kegg_id": "D00109", "name": "Aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"}]
        ),
        "drugbank": pd.DataFrame(
            [{"drugbank_id": "DB00945", "name": "Aspirin", "smiles": ""}]
        ),
    }
    df = merge_sources(raw)
    assert len(df) == 1
    sources = df.iloc[0]["sources"]
    for src in ["chembl", "drugcentral", "pubchem", "inxight", "kegg"]:
        assert src in sources
    assert "drugbank" not in sources
