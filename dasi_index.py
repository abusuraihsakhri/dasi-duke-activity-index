#!/usr/bin/env python3
"""
Duke Activity Status Index (DASI) & Peak VO2
Calculates DASI score, estimated peak VO2 (mL/kg/min), and METs for functional capacity assessment.

The DASI is a 12-item questionnaire assessing functional capacity. Each item is weighted
based on metabolic demand. Total score ranges 0-58.2, used to estimate peak VO2.

Reference: Hlatky MA, et al. "A brief self-administered questionnaire to determine functional capacity." Am J Cardiol. 1989.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, List, Optional

# DASI questionnaire items with metabolic weights (Hlatky et al. 1989)
DASI_ITEMS = {
    "v1":  {"weight": 1.75, "description": "Take care of yourself (eating, dressing, bathing)"},
    "v2":  {"weight": 1.75, "description": "Walk indoors around the house"},
    "v3":  {"weight": 2.75, "description": "Walk 1-2 blocks on level ground"},
    "v4":  {"weight": 3.50, "description": "Climb a flight of stairs or walk up a hill"},
    "v5":  {"weight": 4.50, "description": "Run a short distance"},
    "v6":  {"weight": 2.70, "description": "Light work around the house (dusting, washing dishes)"},
    "v7":  {"weight": 3.50, "description": "Moderate work around the house (vacuuming, sweeping)"},
    "v8":  {"weight": 5.50, "description": "Heavy work around the house (scrubbing floors, lifting)"},
    "v9":  {"weight": 4.00, "description": "Rake leaves, weed, or garden"},
    "v10": {"weight": 5.25, "description": "Sexual relations"},
    "v11": {"weight": 6.00, "description": "Moderate recreational activities (golf, bowling)"},
    "v12": {"weight": 7.50, "description": "Strenuous sports (swimming, tennis, basketball)"},
}

MAX_DASI_SCORE = 48.7  # Sum of all weights (1.75+1.75+2.75+3.50+4.50+2.70+3.50+5.50+4.00+5.25+6.00+7.50)


def calculate_dasi_score(responses: Dict[str, float]) -> float:
    """
    Calculate DASI score from questionnaire responses.

    Args:
        responses: Dict mapping item keys (v1-v12) to 0 (cannot do) or 1 (can do).

    Returns:
        DASI score (0 to MAX_DASI_SCORE).
    """
    score = 0.0
    for key, config in DASI_ITEMS.items():
        val = responses.get(key, 0)
        if val and float(val) > 0:
            score += config["weight"]
    return round(score, 2)


def estimate_peak_vo2(dasi_score: float) -> float:
    """
    Estimate peak VO2 from DASI score using Hlatky formula:
    peak VO2 (mL/kg/min) = (DASI score * 0.43) + 9.6

    Args:
        dasi_score: DASI total score.

    Returns:
        Estimated peak VO2 in mL/kg/min.
    """
    return round((dasi_score * 0.43) + 9.6, 2)


def calculate_mets(peak_vo2: float) -> float:
    """
    Convert peak VO2 to METs (Metabolic Equivalents).
    1 MET = 3.5 mL/kg/min

    Args:
        peak_vo2: Peak VO2 in mL/kg/min.

    Returns:
        METs value.
    """
    return round(peak_vo2 / 3.5, 2)


def classify_functional_capacity(dasi_score: float, mets: float) -> Dict[str, str]:
    """
    Classify functional capacity based on DASI score and METs.

    Thresholds based on ACC/AHA guidelines:
    - Poor: < 4 METs (DASI < ~10.2)
    - Moderate: 4-7 METs (DASI ~10.2-34.7)
    - Good: > 7 METs (DASI > ~34.7)

    Args:
        dasi_score: DASI total score.
        mets: Estimated METs.

    Returns:
        Dict with classification and clinical recommendation.
    """
    if mets < 4.0:
        return {
            "classification": "Poor Functional Capacity",
            "clinical_recommendation": "Consider preoperative cardiac testing; high surgical risk"
        }
    elif mets < 7.0:
        return {
            "classification": "Moderate Functional Capacity",
            "clinical_recommendation": "Moderate surgical risk; clinical judgment for further testing"
        }
    else:
        return {
            "classification": "Good Functional Capacity",
            "clinical_recommendation": "Low surgical risk; proceed without additional cardiac testing"
        }


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Core DASI algorithm: calculate score, peak VO2, METs, and classification.

    Accepts either:
    - Individual DASI items (v1-v12) as 0/1 responses
    - A pre-computed 'dasi_score' value

    Returns:
        Dict with score, peak_vo2, mets, classification, and clinical_recommendation.
    """
    # If dasi_score is provided directly, use it
    if "dasi_score" in kwargs and kwargs["dasi_score"] is not None:
        try:
            dasi_score = float(kwargs["dasi_score"])
        except (ValueError, TypeError):
            dasi_score = 0.0
    else:
        # Build responses dict from individual items
        responses = {}
        for key in DASI_ITEMS:
            if key in kwargs:
                try:
                    responses[key] = float(kwargs[key])
                except (ValueError, TypeError):
                    responses[key] = 0.0
        dasi_score = calculate_dasi_score(responses)

    # Clamp score to valid range
    dasi_score = max(0.0, min(dasi_score, MAX_DASI_SCORE))

    peak_vo2 = estimate_peak_vo2(dasi_score)
    mets = calculate_mets(peak_vo2)
    classification = classify_functional_capacity(dasi_score, mets)

    return {
        "tool": "dasi-duke-activity-index",
        "dasi_score": dasi_score,
        "peak_vo2_ml_kg_min": peak_vo2,
        "mets": mets,
        "classification": classification["classification"],
        "clinical_recommendation": classification["clinical_recommendation"],
        "max_possible_score": MAX_DASI_SCORE,
        "inputs_evaluated": len([k for k in kwargs if k.startswith("v") and k in DASI_ITEMS]),
    }


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    kwargs.pop("command", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def process_batch(input_csv: str, output_csv: str) -> None:
    import os
    input_path = os.path.abspath(input_csv)
    output_path = os.path.abspath(output_csv)

    if not os.path.isfile(input_csv):
        raise FileNotFoundError(f"Input CSV file not found: {input_csv}")

    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if not fieldnames:
        raise ValueError(f"Input CSV file is empty or has no headers: {input_csv}")

    out_fields = fieldnames + ["dasi_score", "peak_vo2_ml_kg_min", "mets", "classification", "clinical_recommendation"]
    out_rows = []

    for r in rows:
        calc_res = calculate_metrics(**r)
        row_dict = dict(r)
        row_dict["dasi_score"] = calc_res["dasi_score"]
        row_dict["peak_vo2_ml_kg_min"] = calc_res["peak_vo2_ml_kg_min"]
        row_dict["mets"] = calc_res["mets"]
        row_dict["classification"] = calc_res["classification"]
        row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
        out_rows.append(row_dict)

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.isdir(output_dir):
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {output_csv}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Duke Activity Status Index (DASI) & Peak VO2 Calculator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser - DASI questionnaire items
    single_parser = subparsers.add_parser("single", help="Evaluate single case using DASI questionnaire")
    single_parser.add_argument("--dasi-score", type=float, help="Pre-computed DASI score (0-58.2)")
    for key, config in DASI_ITEMS.items():
        single_parser.add_argument(
            f"--{key}", type=float, default=None,
            help=f"{config['description']} (weight: {config['weight']}) - 0 or 1"
        )
    single_parser.set_defaults(func=process_single)

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV with DASI responses")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV with DASI items (v1-v12)")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    try:
        if args.command == "single":
            args.func(args)
        elif args.command == "batch":
            process_batch(args.input, args.output)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
