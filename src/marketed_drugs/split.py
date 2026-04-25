"""hepatotoxic flag로 all/non_hepatotoxic 분리."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def split_by_hepatotoxic(df: pd.DataFrame, output_root: Path) -> dict[str, Path]:
    """`all/marketed_all.csv`와 `non_hepatotoxic/marketed_clean.csv` 동시 저장."""
    all_dir = output_root / "all"
    clean_dir = output_root / "non_hepatotoxic"
    all_dir.mkdir(parents=True, exist_ok=True)
    clean_dir.mkdir(parents=True, exist_ok=True)

    all_path = all_dir / "marketed_all.csv"
    clean_path = clean_dir / "marketed_clean.csv"

    df.to_csv(all_path, index=False)
    clean = df[df["known_hepatotoxic"] == 0].reset_index(drop=True)
    clean.to_csv(clean_path, index=False)

    logger.info("Split: all=%d, non_hepatotoxic=%d", len(df), len(clean))
    return {"all": all_path, "clean": clean_path}
