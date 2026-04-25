import json
from unittest.mock import patch

from src.marketed_drugs.inxight import collect_inxight


def test_inxight_parses_marketed(fixtures_dir):
    fixture = json.loads((fixtures_dir / "inxight_dump.json").read_text())

    with patch("src.marketed_drugs.inxight.fetch_json", return_value=fixture):
        df = collect_inxight()

    assert len(df) == 2
    assert set(df.columns) >= {"unii", "name", "smiles", "inchi_key", "marketing_status"}
    aspirin = df[df["name"] == "Aspirin"].iloc[0]
    assert aspirin["smiles"] == "CC(=O)Oc1ccccc1C(=O)O"
    assert aspirin["unii"] == "R16CO5Y76E"
