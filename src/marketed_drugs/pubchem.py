"""PubChem FDA Approved Drugs 분류 수집."""

from __future__ import annotations

import logging
import time
from urllib.parse import quote

import pandas as pd

from src.marketed_drugs._http import fetch_json

logger = logging.getLogger(__name__)

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
SOURCE_NAME = "FDA Pharmaceutical Substances"
RATE_LIMIT_DELAY = 0.2
BATCH_SIZE = 200


def _fetch_cids() -> list[int]:
    """FDA 승인 약물 CID 리스트 조회."""
    url = f"{PUBCHEM_BASE}/sourceall/{quote(SOURCE_NAME)}/cids/JSON"
    data = fetch_json(url)
    return data.get("IdentifierList", {}).get("CID", [])


def _fetch_properties(cids: list[int]) -> list[dict]:
    """CID 배치별로 SMILES + InChIKey + Title 조회."""
    rows: list[dict] = []
    for i in range(0, len(cids), BATCH_SIZE):
        batch = cids[i : i + BATCH_SIZE]
        cid_str = ",".join(str(c) for c in batch)
        url = (
            f"{PUBCHEM_BASE}/compound/cid/{cid_str}/property/"
            "Title,CanonicalSMILES,InChIKey/JSON"
        )
        data = fetch_json(url)
        props = data.get("PropertyTable", {}).get("Properties", [])
        rows.extend(props)
        time.sleep(RATE_LIMIT_DELAY)
    return rows


def collect_pubchem() -> pd.DataFrame:
    """PubChem FDA Pharmaceutical Substances 전체 수집."""
    cids = _fetch_cids()
    logger.info("PubChem: %d CID 발견", len(cids))

    props = _fetch_properties(cids)

    df = pd.DataFrame(
        [
            {
                "cid": p.get("CID"),
                "name": p.get("Title", ""),
                "smiles": p.get("CanonicalSMILES", ""),
                "inchi_key": p.get("InChIKey", ""),
            }
            for p in props
        ]
    )
    if not df.empty:
        df = df[df["smiles"].notna() & (df["smiles"] != "")]
    logger.info("PubChem: %d 약물 수집", len(df))
    return df.reset_index(drop=True)
