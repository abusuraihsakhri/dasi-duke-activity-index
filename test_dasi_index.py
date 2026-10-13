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
    # v1(2.75) + v2(1.75) + v3(2.75) = 7.25
    assert res["dasi_score"] == 7.25


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

def test_published_weights_and_threshold():
    from dasi_index import DASI_ITEMS, classify_functional_capacity
    assert [v["weight"] for v in DASI_ITEMS.values()] == [
        2.75, 1.75, 2.75, 5.50, 8.00, 2.70, 3.50, 8.00,
        4.50, 5.25, 6.00, 7.50
    ]
    assert MAX_DASI_SCORE == 58.2
    assert "limited" in classify_functional_capacity(34, 6.9)["classification"]
    assert "higher" in classify_functional_capacity(34.01, 6.9)["classification"]


@pytest.mark.parametrize("response", [None, "no", "NaN", float("inf"), -1, 0.5, 2])
def test_nonbinary_response_rejected(response):
    with pytest.raises(ValueError):
        calculate_dasi_score({"v1": response})


@pytest.mark.parametrize("score", ["not-a-number", "nan", float("inf"), -1, 58.21])
def test_invalid_score_rejected(score):
    with pytest.raises(ValueError):
        calculate_metrics(dasi_score=score)


def test_mixed_input_rejected():
    with pytest.raises(ValueError):
        calculate_metrics(dasi_score=10, v1=1)


def test_batch_with_preexisting_score_column(tmp_path):
    source = tmp_path / "source.csv"
    output = tmp_path / "result.csv"
    source.write_text("sample,dasi_score\nX,58.2\n", encoding="utf-8")
    process_batch(str(source), str(output))
    assert output.read_text(encoding="utf-8").splitlines()[0].count("dasi_score") == 1


def test_empty_dasi_assessment_is_rejected():
    with pytest.raises(ValueError):
        calculate_metrics()


def test_batch_neutralizes_spreadsheet_formulas(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text('case,v1\n"=1+1",1\n', encoding="utf-8")
    process_batch(str(csv_in), str(csv_out))
    import csv
    with csv_out.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["case"] == "'=1+1"
    assert row["dasi_score"] == "2.75"
