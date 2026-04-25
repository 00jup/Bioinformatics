from src.marketed_drugs.merge import canonicalize_smiles, smiles_to_inchikey


def test_canonical_normalizes_equivalent_forms():
    assert canonicalize_smiles("CCO") == canonicalize_smiles("OCC")
    assert canonicalize_smiles("c1ccccc1") == canonicalize_smiles("C1=CC=CC=C1")


def test_canonical_keeps_largest_fragment():
    salt = "CC(=O)Oc1ccccc1C(=O)[O-].[Na+]"
    expected = canonicalize_smiles("CC(=O)Oc1ccccc1C(=O)O")
    assert canonicalize_smiles(salt) == expected


def test_canonical_invalid_returns_none():
    assert canonicalize_smiles("not_a_smiles") is None
    assert canonicalize_smiles("") is None
    assert canonicalize_smiles(None) is None


def test_inchikey_for_aspirin():
    key = smiles_to_inchikey("CC(=O)Oc1ccccc1C(=O)O")
    assert key.startswith("BSYNRYMUTXBXSQ")
