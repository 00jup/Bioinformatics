from unittest.mock import patch

from src.marketed_drugs.drugbank import collect_drugbank


def test_drugbank_parses_vocab(fixtures_dir):
    csv_text = (fixtures_dir / "drugbank_vocab.csv").read_text()

    with patch("src.marketed_drugs.drugbank.fetch_text", return_value=csv_text):
        df = collect_drugbank()

    assert len(df) == 3
    assert "smiles" in df.columns
    assert (df["smiles"] == "").all()
    assert "inchi_key" in df.columns
    assert "BSYNRYMUTXBXSQ-UHFFFAOYSA-N" in df["inchi_key"].values
