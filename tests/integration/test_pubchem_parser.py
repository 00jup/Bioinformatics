import json
from unittest.mock import patch

from src.marketed_drugs.pubchem import collect_pubchem


def test_pubchem_collects_fda_approved(fixtures_dir):
    fixture = json.loads((fixtures_dir / "pubchem_response.json").read_text())

    def fake_fetch(url, params=None, timeout=30):
        if "/substance/sourceall/" in url:
            return fixture["cid_list"]
        return fixture["properties"]

    with patch("src.marketed_drugs.pubchem.fetch_json", side_effect=fake_fetch):
        df = collect_pubchem()

    assert len(df) == 3
    assert set(df.columns) >= {"cid", "name", "smiles", "inchi_key"}
    assert 2244 in df["cid"].values
