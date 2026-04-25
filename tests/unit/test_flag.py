import pandas as pd

from src.marketed_drugs.flag import flag_hepatotoxic


def test_flag_matches_by_inchikey(fixtures_dir):
    dilirank = pd.read_csv(fixtures_dir / "dilirank_sample.csv")
    df = pd.DataFrame(
        [
            {
                "canonical_smiles": "CC(=O)Nc1ccc(O)cc1",
                "inchi_key": "RZVAJINKPMORJF-UHFFFAOYSA-N",
                "name": "Paracetamol",
            },
            {
                "canonical_smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                "name": "Aspirin",
            },
            {
                "canonical_smiles": "CCO",
                "inchi_key": "LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
                "name": "Ethanol",
            },
        ]
    )
    tdc_pos_inchikeys = {"RZVAJINKPMORJF-UHFFFAOYSA-N"}

    result = flag_hepatotoxic(df, dilirank=dilirank, tdc_pos_inchikeys=tdc_pos_inchikeys)

    assert "known_hepatotoxic" in result.columns
    assert "in_dilirank" in result.columns
    assert "dilirank_category" in result.columns
    assert "in_tdc_dili_pos" in result.columns

    paracetamol = result[result["inchi_key"] == "RZVAJINKPMORJF-UHFFFAOYSA-N"].iloc[0]
    assert paracetamol["known_hepatotoxic"] == 1
    assert paracetamol["dilirank_category"] == "vMost-DILI-Concern"
    assert paracetamol["in_tdc_dili_pos"] == 1

    aspirin = result[result["inchi_key"] == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"].iloc[0]
    assert aspirin["known_hepatotoxic"] == 0
    assert aspirin["dilirank_category"] == "vNo-DILI-Concern"
    assert aspirin["in_tdc_dili_pos"] == 0

    ethanol = result[result["inchi_key"] == "LFQSCWFLJHTTHZ-UHFFFAOYSA-N"].iloc[0]
    assert ethanol["known_hepatotoxic"] == 0
    assert ethanol["dilirank_category"] == "unknown"
    assert ethanol["in_dilirank"] == 0
