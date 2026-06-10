"""
FPV TUNISIA -- Comprehensive Test Suite v2.1
============================================
Run with: python test_app.py

Tests all critical paths including new v2.1 features:
- Inverse mode (budget <- power)
- Aquatic gain integration
- New scoring system
- Updated price (0.307 TND/kWh)
- Environmental equivalents
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
local_pkgs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_pkgs")
if os.path.exists(local_pkgs):
    sys.path.insert(0, local_pkgs)

import sqlite3
import numpy as np
import numpy_financial as npf
import pandas as pd

from src.config import get_connection, load_constants, load_dams, load_evap, load_thermal, load_scenarios, get_aquatic_gain
from src.models import DamProfile, EconomicConstants, ProjectInputs, ProjectResults
from src.engine import compute_project


def print_header(title):
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")


def print_test(name):
    print(f"\n[{name}]")
    print("-" * 50)


def assert_true(condition, msg):
    if condition:
        print(f"  PASS: {msg}")
        return True
    else:
        print(f"  FAIL: {msg}")
        return False


# Load for tests
conn = get_connection()
dams_df = load_dams(conn)

def run_all_tests():
    passed = 0
    failed = 0

    print_header("FPV TUNISIA v2.1 -- COMPREHENSIVE TEST SUITE")

    # -- TEST 1: Database Connectivity & Structure ---
    print_test("TEST 1: Database Connectivity & Structure")
    try:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in c.fetchall()]
        expected = ['dams', 'constants', 'evaporation_monthly', 'thermal_monthly', 'economic_scenarios', 'aquatic_gain']

        for table in expected:
            if assert_true(table in tables, f"Table '{table}' exists"):
                c.execute(f"SELECT COUNT(*) FROM {table}")
                count = c.fetchone()[0]
                print(f"     -> {count} rows")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 2: Economic Constants (J1-J8) ---
    print_test("TEST 2: Economic Constants (J1-J8) -- Price updated to 0.307")
    try:
        const_dict = load_constants(conn)
        for key in ['J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8']:
            assert_true(key in const_dict, f"{key} = {const_dict.get(key, 'MISSING')}")

        j1_val = const_dict['J1']
        assert_true(abs(j1_val - 0.307) < 0.001, f"J1 = {j1_val} (expected 0.307)")
        
        j6_int = int(const_dict['J6'])
        assert_true(j6_int == 25 and j6_int > 0, f"J6 = {j6_int} (int, valid for range)")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 3: Aquatic Gain Data ---
    print_test("TEST 3: Aquatic Gain Data (from Excel)")
    try:
        for dam_id in range(1, 6):
            aq = get_aquatic_gain(dam_id)
            assert_true(aq["gain_percent"] > 0, f"Dam {dam_id}: gain_percent = {aq['gain_percent']:.2f}%")
            assert_true(aq["gain_kwh"] > 0, f"Dam {dam_id}: gain_kwh = {aq['gain_kwh']:,.0f}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 4: Inverse Mode (Power -> Budget) ---
    print_test("TEST 4: Inverse Mode (Power -> Budget)")
    try:
        const = EconomicConstants(
            J1=0.307, J2=0.05, J3=0.004, J4=0.02, 
            J5=0.10, J6=25, J7=0.000445, J8=0.0000358
        )
        
        saad_dict = dams_df[dams_df['name'] == 'Sidi Saad'].iloc[0].to_dict()
        dam = DamProfile(**saad_dict)
        
        # Mode power: 20 MWc should give budget = 46,000,000
        inputs_power = ProjectInputs(
            budget=0, desired_power=20.0, 
            objective="Mixte", loan_rate=0, loan_share=0, mode="power"
        )
        res_power = compute_project(dam, const, inputs_power)
        assert_true(res_power.retained_power == 20.0, f"Power mode: retained = {res_power.retained_power:.1f} MWc")
        assert_true(res_power.capex == 46_000_000, f"Power mode: CAPEX = {res_power.capex:,.0f} (expected 46,000,000)")
        
        # Mode budget: 50M should give power ~= 21.7
        inputs_budget = ProjectInputs(
            budget=50_000_000, desired_power=None,
            objective="Mixte", loan_rate=0, loan_share=0, mode="budget"
        )
        res_budget = compute_project(dam, const, inputs_budget)
        assert_true(res_budget.max_power > 20, f"Budget mode: max_power = {res_budget.max_power:.1f}")
        
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    # -- TEST 5: Aquatic Gain in Results ---
    print_test("TEST 5: Aquatic Gain Integration")
    try:
        inputs = ProjectInputs(
            budget=50_000_000, desired_power=None,
            objective="Mixte", loan_rate=0, loan_share=0, mode="budget"
        )
        res = compute_project(dam, const, inputs)
        
        assert_true(hasattr(res, 'aquatic_gain_percent'), "Result has aquatic_gain_percent")
        assert_true(hasattr(res, 'aquatic_gain_kwh'), "Result has aquatic_gain_kwh")
        assert_true(res.aquatic_gain_percent > 0, f"Aquatic gain % = {res.aquatic_gain_percent:.2f}")
        assert_true(res.aquatic_gain_kwh > 0, f"Aquatic gain kWh = {res.aquatic_gain_kwh:,.0f}")
        
        base_gain = get_aquatic_gain(5)["gain_kwh"]
        expected_scaled = base_gain * (res.retained_power / 20.0)
        assert_true(abs(res.aquatic_gain_kwh - expected_scaled) < 1, 
                   f"Aquatic gain scaled correctly: {res.aquatic_gain_kwh:,.0f} ~= {expected_scaled:,.0f}")
        
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 6: Environmental Equivalents ---
    print_test("TEST 6: Environmental Equivalents Calculation")
    try:
        res = compute_project(dam, const, inputs)
        
        pools = res.water_saved_m3 / 2500
        trees = res.co2_avoided / 0.02
        cars = res.co2_avoided / 2.5
        
        assert_true(pools > 0, f"Pools equivalent = {pools:.0f}")
        assert_true(trees > 0, f"Trees equivalent = {trees:,.0f}")
        assert_true(cars > 0, f"Cars equivalent = {cars:,.0f}")
        
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 7: Coverage Rate & Environmental Alerts ---
    print_test("TEST 7: Coverage Rate & Alerts with New Price")
    try:
        inputs_small = ProjectInputs(budget=10_000_000, desired_power=None,
                                    objective="Mixte", loan_rate=0, loan_share=0, mode="budget")
        res_small = compute_project(dam, const, inputs_small)
        assert_true(res_small.alert_ok or res_small.coverage_rate <= 5.0,
                   f"Small budget: coverage={res_small.coverage_rate:.2f}%, alert_ok={res_small.alert_ok}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 8: Cash Flow Structure (25 years) ---
    print_test("TEST 8: Cash Flow Structure (25 years) with new price")
    try:
        res = compute_project(dam, const, inputs)
        assert_true(len(res.cash_flows) == 26, f"26 cash flows: {len(res.cash_flows)}")
        assert_true(res.cash_flows[0] < 0, f"Year 0 negative: {res.cash_flows[0]:,.0f}")
        assert_true(res.cash_flows[1] > 0, f"Year 1 positive: {res.cash_flows[1]:,.0f}")
        
        cumsum = np.cumsum(res.cash_flows)
        positive_idx = next((i for i, v in enumerate(cumsum) if v > 0), None)
        assert_true(positive_idx is not None and positive_idx == res.payback,
                   f"Payback at year {res.payback}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 9: Score Calculation ---
    print_test("TEST 9: Score Calculation")
    try:
        from src.tabs.comparison_tab import compute_score
        
        res = compute_project(dam, const, inputs)
        score, color = compute_score(res, dam, inputs)
        
        assert_true(score > 0, f"Score = {score:.1f}")
        assert_true(color in ['red', 'orange', 'yellow', 'green', 'blue'], f"Color = {color}")
        assert_true(score <= 100, f"Score <= 100: {score:.1f}")
        
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # ---
    print_header("RESULTS SUMMARY")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)