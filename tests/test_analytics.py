"""Unit tests for Stage 4 Sales Analytics calculations."""

import pandas as pd
import pytest
from ui.page_analytics import (
    compute_funnel_metrics,
    compute_lead_leakage_metrics,
    compute_lead_source_metrics,
    compute_segment_metrics,
    load_leads_data,
    simulate_funnel_recovery,
)


def test_funnel_integrity():
    """Verify cumulative funnel numbers match dataset records exactly."""
    df = load_leads_data()
    funnel = compute_funnel_metrics(df)
    
    # 5,000 total leads
    assert funnel.loc[funnel["Stage"] == "1. Lead Generated", "Count"].values[0] == 5000
    # 368 activated
    assert funnel.loc[funnel["Stage"] == "6. Activated", "Count"].values[0] == 368
    # Cumulative percentages
    assert funnel.loc[funnel["Stage"] == "6. Activated", "Cumulative_Pct"].values[0] == 7.36
    # Intermediate stages
    assert funnel.loc[funnel["Stage"] == "2. Contacted", "Count"].values[0] == 3406
    assert funnel.loc[funnel["Stage"] == "3. Needs Assessed", "Count"].values[0] == 1974
    assert funnel.loc[funnel["Stage"] == "4. Quote Accepted", "Count"].values[0] == 861
    assert funnel.loc[funnel["Stage"] == "5. KYC Complete", "Count"].values[0] == 588


def test_segment_metrics_and_cac():
    """Verify segment CAC per activation = total cost / activations."""
    df = load_leads_data()
    seg = compute_segment_metrics(df).set_index("Segment")

    # Micro retail
    micro = seg.loc["Micro retail & services"]
    assert micro["Total Leads"] == 2709
    assert micro["Activated"] == 110
    assert micro["Conversion %"] == 4.06
    assert micro["Total Spend (₹)"] == 2200780
    assert round(micro["CAC / Activation (₹)"], 2) == 20007.09

    # Small multi-site
    multi = seg.loc["Small multi-site businesses"]
    assert multi["Total Leads"] == 755
    assert multi["Activated"] == 83
    assert multi["Conversion %"] == 10.99
    assert round(multi["LTV / CAC"], 2) == 37.88

    # Small manufacturers
    mfg = seg.loc["Small manufacturers"]
    assert mfg["Total Leads"] == 289
    assert mfg["Activated"] == 37
    assert mfg["Conversion %"] == 12.80

    # Professional offices
    prof = seg.loc["Professional offices"]
    assert prof["Total Leads"] == 1247
    assert prof["Activated"] == 138
    assert round(prof["CAC / Activation (₹)"], 2) == 10694.71


def test_lead_source_metrics():
    """Verify lead source conversion rankings."""
    df = load_leads_data()
    src = compute_lead_source_metrics(df).set_index("Lead Source")

    # Total leads sum to 5000
    assert src["Leads"].sum() == 5000
    # Total activations sum to 368
    assert src["Activated"].sum() == 368
    # Referral has highest conversion rate
    assert src.loc["Referral", "Conversion %"] == 14.77
    assert src.loc["Referral", "Activated"] == 61


def test_where_leads_leak_addressable_drops():
    """
    Verify addressable drop analysis:
    Total addressable drops must equal exactly 2,106 of 4,632.
    Breakdown:
      - Self-serve flow: 827
      - Instant quote + budget fit: 1,006
      - Smart KYC: 273
    """
    df = load_leads_data()
    leakage_df, total_addr, total_dropped = compute_lead_leakage_metrics(df)

    assert total_dropped == 4632
    assert total_addr == 2106
    assert round(total_addr / total_dropped * 100, 2) == 45.47

    addr_by_mod = leakage_df[leakage_df["Addressable"]].groupby("Addressing Accel Module")["Drop Count"].sum()
    assert addr_by_mod["Self-serve flow"] == 827
    assert addr_by_mod["Instant quote + budget fit"] == 1006
    assert addr_by_mod["Smart KYC"] == 273


def test_what_if_funnel_recovery_simulation():
    """
    Verify what-if funnel simulator with 30% recovery rate:
    - Baseline: 368 activations (7.36%)
    - Additional activations: ~+118 (118.07)
    - Projected live: ~486
    - Projected conversion: ~9.72%
    """
    df = load_leads_data()
    res = simulate_funnel_recovery(df, recovery_rate=0.30)

    assert res["baseline_activations"] == 368
    assert res["baseline_conversion_pct"] == 7.36
    assert round(res["additional_activations"]) == 118
    assert round(res["projected_activations"]) == 486
    assert round(res["projected_conversion_pct"], 1) == 9.7
    assert 9.70 <= res["projected_conversion_pct"] <= 9.75
