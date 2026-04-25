from unittest.mock import patch

from src.marketed_drugs.kegg import collect_kegg, parse_kegg_entry, parse_kegg_list


def test_parse_kegg_list(fixtures_dir):
    text = (fixtures_dir / "kegg_list.txt").read_text()
    rows = parse_kegg_list(text)
    assert len(rows) == 3
    assert rows[0]["kegg_id"] == "D00109"
    assert "Aspirin" in rows[0]["name"]


def test_parse_kegg_entry_extracts_atc(fixtures_dir):
    text = (fixtures_dir / "kegg_entry.txt").read_text()
    info = parse_kegg_entry(text)
    assert info["atc_code"] == "A01AD05;B01AC06;N02BA01"
    assert info["pubchem_cid"] == "7517"


def test_collect_kegg_uses_pubchem_for_smiles(fixtures_dir):
    list_text = (fixtures_dir / "kegg_list.txt").read_text()
    entry_text = (fixtures_dir / "kegg_entry.txt").read_text()

    def fake_fetch(url, params=None, timeout=60):
        if "/list/" in url:
            return list_text
        return entry_text

    with patch("src.marketed_drugs.kegg.fetch_text", side_effect=fake_fetch), patch(
        "src.marketed_drugs.kegg._smiles_from_pubchem_cid",
        return_value="CC(=O)Oc1ccccc1C(=O)O",
    ):
        df = collect_kegg(limit=3)

    assert len(df) >= 1
    aspirin = df[df["kegg_id"] == "D00109"].iloc[0]
    assert aspirin["smiles"] == "CC(=O)Oc1ccccc1C(=O)O"
