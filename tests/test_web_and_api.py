"""Web questionnaire alignment and DASI API validation tests."""
import json
import re
from pathlib import Path

import pytest
from fastapi import HTTPException

from dasi_index import DASI_ITEMS, MAX_DASI_SCORE
from agents.api import DasiRequest, api_dasi, index

HTML = Path(__file__).resolve().parents[1] / "web" / "index.html"


def test_browser_weights_match_python_source():
    page = HTML.read_text(encoding="utf-8")
    matched = re.search(r"const activities = (\[[\s\S]*?\]);", page)
    assert matched, "Browser questionnaire weights are missing"
    pairs = json.loads(matched.group(1))
    assert len(pairs) == 12
    assert [weight for _, weight in pairs] == [
        item["weight"] for item in DASI_ITEMS.values()
    ]
    assert round(sum(weight for _, weight in pairs), 2) == MAX_DASI_SCORE


def test_html_has_no_simulated_or_fabricated_audit():
    page = HTML.read_text(encoding="utf-8")
    assert "DOSSIER-SIM" not in page
    assert "HMAC_SHA256_e83" not in page
    assert "fetch('/api/audit'" not in page
    assert "dasi-form" in page


def test_api_all_yes_and_none():
    yes = api_dasi(DasiRequest(responses={key: 1 for key in DASI_ITEMS}))
    no = api_dasi(DasiRequest(responses={key: 0 for key in DASI_ITEMS}))
    assert yes["dasi_score"] == 58.2
    assert no["dasi_score"] == 0
    assert yes["inputs_evaluated"] == 12


def test_api_rejects_incomplete_and_fractional():
    with pytest.raises(HTTPException) as e:
        api_dasi(DasiRequest(responses={"v1": 1}))
    assert e.value.status_code == 422
    with pytest.raises(HTTPException) as e:
        api_dasi(DasiRequest(responses={**{key: 1 for key in DASI_ITEMS}, "v1": 2}))
    assert e.value.status_code == 422


def test_api_root_serves_static_questionnaire():
    response = index()
    assert Path(response.path).is_file()
    assert str(response.path).endswith("web/index.html")
