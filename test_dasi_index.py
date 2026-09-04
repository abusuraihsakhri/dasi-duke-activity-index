import pytest
from dasi_index import calculate_metrics, process_batch, calculate_dasi_score, estimate_peak_vo2, calculate_mets, MAX_DASI_SCORE


def test_dasi_index_single():
    """Test basic DASI calculation with individual items."""
    res = calculate_metrics(v1=1.0, v2=1.0, v3=1.0)
    assert "dasi_score" in res
    assert "classification" in res
    assert "peak_vo2_ml_kg_min" in res
    assert "mets" in res
    assert res["dasi_score"] > 0
    # v1(1.75) + v2(1.75) + v3(2.75) = 6.25
    assert res["dasi_score"] == 6.25


def test_dasi_score_calculation():
    """Test DASI score calculation with all items."""
    # All items = 1 (can do all activities)
    responses = {f"v{i}": 1.0 for i in range(1, 13)}
    score = calculate_dasi_score(responses)
    assert score == MAX_DASI_SCORE

    # No items = 0 (cannot do any activities)
    responses = {f"v{i}": 0.0 for i in range(1, 13)}
    score = calculate_dasi_score(responses)
    assert score == 0.0


def test_peak_vo2_estimation():
    """Test peak VO2 estimation from DASI score."""
    # Score of 0 should give baseline VO2
    vo2 = estimate_peak_vo2(0.0)
    assert vo2 == 9.6  # (0 * 0.43) + 9.6

    # Score of 58.2 (max)
    vo2 = estimate_peak_vo2(58.2)
    assert vo2 == round((58.2 * 0.43) + 9.6, 2)


def test_mets_calculation():
    """Test METs calculation from peak VO2."""
    mets = calculate_mets(35.0)
    assert mets == 10.0  # 35 / 3.5


def test_dasi_index_batch(tmp_path):
    """Test batch CSV processing."""
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient_ID,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12\nPat_001,1,1,1,1,0,1,0,0,0,0,0,0\nPat_002,1,1,0,0,0,0,0,0,0,0,0,0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "dasi_score" in content
    assert "peak_vo2_ml_kg_min" in content
    assert "mets" in content


def test_dasi_index_batch_missing_file(tmp_path):
    """Test batch processing with missing input file."""
    with pytest.raises(FileNotFoundError):
        process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))


def test_dasi_index_batch_empty_csv(tmp_path):
    """Test batch processing with empty CSV."""
    csv_in = tmp_path / "empty.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="empty or has no headers"):
        process_batch(str(csv_in), str(csv_out))


def test_precomputed_dasi_score():
    """Test using a pre-computed DASI score."""
    res = calculate_metrics(dasi_score=41.7)
    assert res["dasi_score"] == 41.7
    assert res["peak_vo2_ml_kg_min"] == round((41.7 * 0.43) + 9.6, 2)
    assert res["mets"] == round(res["peak_vo2_ml_kg_min"] / 3.5, 2)
