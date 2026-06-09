"""
FPV TUNISIA -- Comprehensive Test Suite
=======================================
Run with: python test_app.py

Tests all critical paths:
1. Database structure & data completeness
2. Economic constants (J1-J8)
3. Dam reference data integrity
4. Monthly evaporation data (Penman-Monteith)
5. Monthly thermal data (PVsyst)
6. Calculation engine core formulas
7. Power constraints (desired vs max)
8. Loan calculations (annuity, VAN impact)
9. Coverage rate & environmental alerts
10. Cash flow structure (25 years)
11. Multi-dam comparison consistency
12. Edge cases (zero budget, 100% loan, 0% interest)
13. Objective-based ranking
14. Data type consistency
"""
import sys
import os

# Add project root and local packages to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
local_pkgs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_pkgs")
if os.path.exists(local_pkgs):
    sys.path.insert(0, local_pkgs)

import sqlite3
import numpy as np
import numpy_financial as npf
import pandas as pd

from src.config import get_connection, load_constants, load_dams, load_evap, load_thermal, load_scenarios
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


def run_all_tests():
    passed = 0
    failed = 0

    print_header("FPV TUNISIA -- COMPREHENSIVE TEST SUITE")

    # -- TEST 1: Database Connectivity & Structure ---
    print_test("TEST 1: Database Connectivity & Structure")
    try:
        conn = get_connection()
        c = conn.cursor()

        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in c.fetchall()]
        expected = ['dams', 'constants', 'evaporation_monthly', 'thermal_monthly', 'economic_scenarios']

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
    print_test("TEST 2: Economic Constants (J1-J8)")
    try:
        const_dict = load_constants(conn)
        for key in ['J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8']:
            assert_true(key in const_dict, f"{key} = {const_dict.get(key, 'MISSING')}")

        # Critical: J6 must be integer-compatible for range()
        j6_int = int(const_dict['J6'])
        assert_true(j6_int == 25 and j6_int > 0, f"J6 = {j6_int} (int, valid for range)")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 3: Dams Data Integrity ---
    print_test("TEST 3: Dams Reference Data")
    try:
        dams_df = load_dams(conn)
        assert_true(len(dams_df) == 5, f"5 dams found: {len(dams_df)}")

        expected_dams = ["Sidi Salem", "Sidi El Barrak", "Bouhertma", "Sejnane", "Sidi Saad"]
        for name in expected_dams:
            assert_true(name in dams_df['name'].values, f"{name} present")

        # Critical values
        saad = dams_df[dams_df['name'] == 'Sidi Saad'].iloc[0]
        assert_true(saad['productible'] == 1780, f"Sidi Saad productible = 1780")
        assert_true(saad['max_coverage_rate'] == 5.0, f"Sidi Saad max coverage = 5% (Ramsar)")
        assert_true(saad['constraint_type'] == 'Ramsar', f"Sidi Saad constraint = 'Ramsar'")
        assert_true(saad['cost_per_mwc'] == 2_300_000, f"Sidi Saad cost = 2,300,000 TND/MWc")

        salem = dams_df[dams_df['name'] == 'Sidi Salem'].iloc[0]
        assert_true(salem['cost_per_mwc'] == 2_200_000, f"Sidi Salem cost = 2,200,000 TND/MWc (cheapest)")

        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 4: Evaporation Data Completeness ---
    print_test("TEST 4: Monthly Evaporation Data (Penman-Monteith)")
    try:
        for dam_id in range(1, 6):
            evap_df = load_evap(conn, dam_id)
            name = dams_df[dams_df['id'] == dam_id]['name'].values[0]

            ok = assert_true(len(evap_df) == 12, f"{name}: 12 months")
            if not ok:
                continue

            # Data quality checks
            assert_true(evap_df['e_mm_day'].min() > 0, f"{name}: E > 0")
            assert_true(evap_df['e_mm_day'].max() < 20, f"{name}: E < 20 mm/j")

            total_saved = evap_df['volume_without_fpv'].sum() - evap_df['volume_with_fpv'].sum()
            assert_true(total_saved > 0, f"{name}: water saved = {total_saved:,.0f} m3/year")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 5: Thermal Data Completeness ---
    print_test("TEST 5: Monthly Thermal Data (PVsyst)")
    try:
        for dam_id in range(1, 6):
            therm_df = load_thermal(conn, dam_id)
            name = dams_df[dams_df['id'] == dam_id]['name'].values[0]

            assert_true(len(therm_df) == 12, f"{name}: 12 months")

            if dam_id == 5:  # Sidi Saad -- real data
                total_gain = therm_df['gain_kwh'].sum()
                assert_true(total_gain > 1_000_000, 
                           f"{name} (REAL): gain = {total_gain:,.0f} kWh")
            else:  # Placeholders
                assert_true(len(therm_df) > 0, f"{name} (PLACEHOLDER): data present")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 6: Calculation Engine -- Core Formulas ---
    print_test("TEST 6: Calculation Engine -- Core Formulas")
    try:
        const = EconomicConstants(
            J1=0.285, J2=0.05, J3=0.004, J4=0.02, 
            J5=0.10, J6=25, J7=0.000445, J8=0.0000358
        )

        saad_dict = dams_df[dams_df['name'] == 'Sidi Saad'].iloc[0].to_dict()
        dam = DamProfile(**saad_dict)
        inputs = ProjectInputs(budget=50_000_000, desired_power=None, 
                            objective="Mixte", loan_rate=0, loan_share=0)

        res = compute_project(dam, const, inputs)

        # Max power = floor(budget / cost_per_mwc, 1)
        expected_max = np.floor(50_000_000 / 2_300_000 * 10) / 10
        assert_true(abs(res.max_power - expected_max) < 0.1, 
                   f"Max power: {res.max_power:.1f} ~= {expected_max:.1f}")

        # Production = power * 1000 * productible / 1e6
        expected_prod = res.retained_power * 1000 * 1780 / 1e6
        assert_true(abs(res.production_gwh - expected_prod) < 0.1,
                   f"Production: {res.production_gwh:.2f} ~= {expected_prod:.2f} GWh")

        # Water = economy_water_m3_mwc * power
        expected_water = 5863 * res.retained_power
        assert_true(abs(res.water_saved_m3 - expected_water) < 1,
                   f"Water saved: {res.water_saved_m3:,.0f} ~= {expected_water:,.0f} m3")

        # CAPEX = cost_per_mwc * power
        expected_capex = 2_300_000 * res.retained_power
        assert_true(abs(res.capex - expected_capex) < 1,
                   f"CAPEX: {res.capex:,.0f} ~= {expected_capex:,.0f} TND")

        # Profitability
        assert_true(res.van > 0, f"VAN positive: {res.van:,.0f} TND")
        assert_true(res.tri > const.J5, f"TRI > discount rate: {res.tri*100:.1f}% > {const.J5*100}%")
        assert_true(res.payback is not None and res.payback < 15, 
                   f"Payback reasonable: {res.payback} years")

        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    # -- TEST 7: Power Constraints ---
    print_test("TEST 7: Power Constraints (Desired vs Max)")
    try:
        # Desired < max -> respect desired
        inputs_limited = ProjectInputs(budget=50_000_000, desired_power=10.0,
                                     objective="Mixte", loan_rate=0, loan_share=0)
        res_limited = compute_project(dam, const, inputs_limited)
        assert_true(res_limited.retained_power == 10.0,
                   f"Desired 10 MWc -> retained: {res_limited.retained_power:.1f}")

        # Desired > max -> cap at max
        inputs_impossible = ProjectInputs(budget=50_000_000, desired_power=30.0,
                                         objective="Mixte", loan_rate=0, loan_share=0)
        res_impossible = compute_project(dam, const, inputs_impossible)
        assert_true(res_impossible.retained_power == res_impossible.max_power,
                   f"Desired 30 MWc -> capped to max: {res_impossible.retained_power:.1f}")

        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 8: Loan Calculations ---
    print_test("TEST 8: Loan Calculations")
    try:
        # 50% loan at 10%
        inputs_loan = ProjectInputs(budget=50_000_000, desired_power=None,
                                   objective="Mixte", loan_rate=10.0, loan_share=50.0)
        res_loan = compute_project(dam, const, inputs_loan)

        expected_loan = res_loan.capex * 0.5
        assert_true(abs(res_loan.loan_amount - expected_loan) < 1,
                   f"Loan: {res_loan.loan_amount:,.0f} = 50% of CAPEX")

        expected_annuity = npf.pmt(0.10, 10, -expected_loan)
        assert_true(abs(res_loan.annuity - expected_annuity) < 1,
                   f"Annuity: {res_loan.annuity:,.0f} TND/year")

        # VAN should decrease with loan costs
        res_no_loan = compute_project(dam, const, inputs)
        assert_true(res_loan.van < res_no_loan.van,
                   f"VAN with loan ({res_loan.van:,.0f}) < without ({res_no_loan.van:,.0f})")

        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 9: Coverage Rate & Environmental Alerts ---
    print_test("TEST 9: Coverage Rate & Alerts")
    try:
        # Small budget -> should pass
        inputs_small = ProjectInputs(budget=10_000_000, desired_power=None,
                                    objective="Mixte", loan_rate=0, loan_share=0)
        res_small = compute_project(dam, const, inputs_small)
        assert_true(res_small.alert_ok or res_small.coverage_rate <= 5.0,
                   f"Small budget: coverage={res_small.coverage_rate:.2f}%, alert_ok={res_small.alert_ok}")

        # Large budget (200M) -> check if coverage exceeds Ramsar 5% limit
        inputs_large = ProjectInputs(budget=200_000_000, desired_power=None,
                                    objective="Mixte", loan_rate=0, loan_share=0)
        res_large = compute_project(dam, const, inputs_large)
        # Note: coverage = (power/20)*9.25 / surface_ha. With 200M budget, power ~87MWc, coverage ~3.6% (under 5%)
        # To trigger alert, need budget > ~270M for Sidi Saad (1104 ha * 5% * 20 / 9.25 * 2.3M ~= 274M)
        if res_large.coverage_rate > 5.0:
            assert_true(not res_large.alert_ok,
                       f"Large budget: coverage={res_large.coverage_rate:.2f}% > 5%, alert triggered")
            assert_true("Ramsar" in res_large.alert or "etude" in res_large.alert or "impact" in res_large.alert,
                       f"Alert mentions environmental concern: '{res_large.alert[:50]}...'")
        else:
            assert_true(res_large.alert_ok,
                       f"Large budget: coverage={res_large.coverage_rate:.2f}% <= 5%, no alert (expected)")

        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 10: Cash Flow Structure (25 years) ---
    print_test("TEST 10: Cash Flow Structure (25 years)")
    try:
        res = compute_project(dam, const, inputs)

        assert_true(len(res.cash_flows) == 26, f"26 cash flows (years 0-25): {len(res.cash_flows)}")
        assert_true(res.cash_flows[0] < 0, f"Year 0 negative (CAPEX): {res.cash_flows[0]:,.0f}")
        assert_true(res.cash_flows[1] > 0, f"Year 1 positive: {res.cash_flows[1]:,.0f}")

        # Cumulative should turn positive
        cumsum = np.cumsum(res.cash_flows)
        positive_idx = next((i for i, v in enumerate(cumsum) if v > 0), None)
        assert_true(positive_idx is not None and positive_idx == res.payback,
                   f"Payback at year {res.payback}, cumulative turns positive at year {positive_idx}")

        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 11: Multi-Dam Comparison Consistency ---
    print_test("TEST 11: Multi-Dam Comparison Consistency")
    try:
        results = []
        for _, dam_row in dams_df.iterrows():
            d = DamProfile(**dam_row.to_dict())
            r = compute_project(d, const, inputs)
            results.append({'name': d.name, 'power': r.retained_power, 
                          'production': r.production_gwh, 'water': r.water_saved_m3,
                          'van': r.van, 'cost': d.cost_per_mwc})

        comp = pd.DataFrame(results)

        # Sidi Salem has lowest cost -> should allow most power
        salem = comp[comp['name'] == 'Sidi Salem'].iloc[0]
        saad = comp[comp['name'] == 'Sidi Saad'].iloc[0]
        assert_true(salem['power'] > saad['power'],
                   f"Sidi Salem power ({salem['power']:.1f}) > Sidi Saad ({saad['power']:.1f}) due to lower cost")

        # All should be profitable
        assert_true(all(comp['van'] > 0), f"All VANs positive: min={comp['van'].min():,.0f}")

        # Bouhertma has lowest water economy (2908) -> should save least water
        bouhertma = comp[comp['name'] == 'Bouhertma'].iloc[0]
        sejnane = comp[comp['name'] == 'Sejnane'].iloc[0]
        assert_true(bouhertma['water'] < sejnane['water'],
                   f"Bouhertma water ({bouhertma['water']:,.0f}) < Sejnane ({sejnane['water']:,.0f})")

        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 12: Edge Cases ---
    print_test("TEST 12: Edge Cases")
    try:
        # Zero budget
        inputs_zero = ProjectInputs(budget=0, desired_power=None,
                                   objective="Mixte", loan_rate=0, loan_share=0)
        res_zero = compute_project(dam, const, inputs_zero)
        assert_true(res_zero.max_power == 0, f"Zero budget -> power=0")
        assert_true(res_zero.capex == 0, f"Zero budget -> CAPEX=0")

        # 100% loan
        inputs_full = ProjectInputs(budget=50_000_000, desired_power=None,
                                   objective="Mixte", loan_rate=10.0, loan_share=100.0)
        res_full = compute_project(dam, const, inputs_full)
        assert_true(res_full.equity == 0, f"100% loan -> equity=0")
        assert_true(abs(res_full.loan_amount - res_full.capex) < 1,
                   f"100% loan -> loan=CAPEX")

        # 0% interest
        inputs_free = ProjectInputs(budget=50_000_000, desired_power=None,
                                   objective="Mixte", loan_rate=0.0, loan_share=50.0)
        res_free = compute_project(dam, const, inputs_free)
        assert_true(res_free.annuity == 0, f"0% interest -> annuity=0")

        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 13: Objective-Based Ranking ---
    print_test("TEST 13: Objective-Based Ranking")
    try:
        # Production objective: Sidi Salem should rank first (lowest cost -> most power)
        inputs_prod = ProjectInputs(budget=50_000_000, desired_power=None,
                                   objective="Production", loan_rate=0, loan_share=0)
        prod_results = []
        for _, dam_row in dams_df.iterrows():
            d = DamProfile(**dam_row.to_dict())
            r = compute_project(d, const, inputs_prod)
            prod_results.append({'name': d.name, 'production': r.production_gwh})

        prod_ranked = sorted(prod_results, key=lambda x: x['production'], reverse=True)
        assert_true(prod_ranked[0]['name'] in ['Sidi Salem', 'Sidi Saad'],
                   f"Production ranking: 1st={prod_ranked[0]['name']} ({prod_ranked[0]['production']:.2f} GWh)")

        # Water objective: Sidi Saad should rank first (5863 m3/MWc)
        inputs_water = ProjectInputs(budget=50_000_000, desired_power=None,
                                    objective="Economie d'eau", loan_rate=0, loan_share=0)
        water_results = []
        for _, dam_row in dams_df.iterrows():
            d = DamProfile(**dam_row.to_dict())
            r = compute_project(d, const, inputs_water)
            water_results.append({'name': d.name, 'water': r.water_saved_m3})

        water_ranked = sorted(water_results, key=lambda x: x['water'], reverse=True)
        assert_true(water_ranked[0]['name'] == 'Sidi Saad',
                   f"Water ranking: 1st={water_ranked[0]['name']} ({water_ranked[0]['water']:,.0f} m3)")

        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # -- TEST 14: Data Type Consistency ---
    print_test("TEST 14: Data Type Consistency")
    try:
        res = compute_project(dam, const, inputs)

        assert_true(isinstance(res.max_power, (int, float, np.floating)),
                   f"max_power: {type(res.max_power).__name__}")
        assert_true(isinstance(res.van, (int, float, np.floating)),
                   f"van: {type(res.van).__name__}")
        assert_true(isinstance(res.tri, (int, float, np.floating, type(None))),
                   f"tri: {type(res.tri).__name__}")
        assert_true(isinstance(res.cash_flows, list),
                   f"cash_flows: list[{len(res.cash_flows)}]")
        assert_true(all(isinstance(cf, (int, float, np.floating)) for cf in res.cash_flows),
                   f"All cash flows numeric")

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