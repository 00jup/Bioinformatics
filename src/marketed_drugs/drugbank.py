"""DrugBank Open Data 어휘 (Tier 2 enrichment, SMILES 미제공)."""

from __future__ import annotations

import io
import logging

import pandas as pd

from src.marketed_drugs._http import fetch_text

logger = logging.getLogger(__name__)

DRUGBANK_OPEN_DATA_URL = (
    "https://go.drugbank.com/releases/latest/downloads/all-drugbank-vocabulary"
)


def collect_drugbank() -> pd.DataFrame:
    """DrugBank Open Data Vocabulary 수집 (SMILES 없음, InChIKey만 보강)."""
    text = fetch_text(DRUGBANK_OPEN_DATA_URL)
    df_raw = pd.read_csv(io.StringIO(text))

    df = pd.DataFrame(
        {
            "drugbank_id": df_raw["DrugBank ID"].astype(str),
            "name": df_raw["Common name"].astype(str),
            "smiles": "",
            "inchi_key": df_raw.get("Standard InChI Key", "").astype(str),
            "unii": df_raw.get("UNII", "").astype(str),
        }
    )
    logger.info("DrugBank: %d 항목 (enrichment 전용, SMILES 미제공)", len(df))
    return df
