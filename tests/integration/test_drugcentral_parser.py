from unittest.mock import patch

from src.marketed_drugs.drugcentral import collect_drugcentral


def test_drugcentral_parses_tsv(fixtures_dir):
    tsv_text = (fixtures_dir / "drugcentral_dump.tsv").read_text()

    with patch("src.marketed_drugs.drugcentral.fetch_text", return_value=tsv_text):
        df = collect_drugcentral()

    assert len(df) == 3
    assert set(df.columns) >= {"drugcentral_id", "name", "smiles", "inchi_key"}
    aspirin = df[df["name"] == "aspirin"].iloc[0]
    assert aspirin["smiles"] == "CC(=O)Oc1ccccc1C(=O)O"
    assert aspirin["inchi_key"] == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
