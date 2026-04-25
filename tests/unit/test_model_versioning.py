import joblib

from src.model_versioning import (
    get_current_version,
    parse_version,
    save_versioned_model,
)


def test_parse_version():
    assert parse_version("1.0.0") == (1, 0, 0)
    assert parse_version("2.5.13") == (2, 5, 13)


def test_get_current_version_from_latest_txt(tmp_path):
    (tmp_path / "latest.txt").write_text("1.5.0")
    assert get_current_version(tmp_path) == "1.5.0"


def test_get_current_version_default_when_missing(tmp_path):
    assert get_current_version(tmp_path) == "1.0.0"


def test_save_versioned_model_creates_dir_and_updates_latest(tmp_path):
    model = {"dummy": True}
    meta = {"version": "1.1.0", "test": "ok"}
    cv = {"auc": 0.9}
    val = {"auc": 0.85}

    save_versioned_model(
        model=model,
        version="1.1.0",
        meta=meta,
        cv_results=cv,
        val_results=val,
        manifest=None,
        models_dir=tmp_path,
    )

    target = tmp_path / "v1.1.0"
    assert target.exists()
    assert (target / "best_model.pkl").exists()
    assert (target / "model_meta.json").exists()
    loaded = joblib.load(target / "best_model.pkl")
    assert loaded == {"dummy": True}
    assert (tmp_path / "latest.txt").read_text().strip() == "1.1.0"
