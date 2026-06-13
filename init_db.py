import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "dams.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- Tables ---
    c.execute("""CREATE TABLE IF NOT EXISTS dams (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        productible REAL,
        economy_water_m3_mwc REAL,
        surface_ha REAL,
        cost_per_mwc REAL,
        constraint_type TEXT,
        max_coverage_rate REAL,
        alert_text TEXT,
        covered_surface_m2 REAL DEFAULT 92489
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS constants (
        key TEXT PRIMARY KEY,
        value REAL,
        description TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS evaporation_monthly (
        id INTEGER PRIMARY KEY,
        dam_id INTEGER,
        month INTEGER,
        month_name TEXT,
        temp_c REAL,
        hr_percent REAL,
        wind_ms REAL,
        rs_kwh_m2_day REAL,
        e_mm_day REAL,
        days INTEGER,
        volume_without_fpv REAL,
        volume_with_fpv REAL,
        FOREIGN KEY (dam_id) REFERENCES dams(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS thermal_monthly (
        id INTEGER PRIMARY KEY,
        dam_id INTEGER,
        month INTEGER,
        month_name TEXT,
        temp_c REAL,
        wind_ms REAL,
        days INTEGER,
        ginc_w_m2_month REAL,
        nb_h_sun INTEGER,
        ginc_w_m2 REAL,
        alpha_ginc_1_eta REAL,
        tcell_terre REAL,
        tcell_float REAL,
        egrid_terre_kwh REAL,
        egrid_float_kwh REAL,
        gain_kwh REAL,
        gain_percent REAL,
        FOREIGN KEY (dam_id) REFERENCES dams(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS economic_scenarios (
        id INTEGER PRIMARY KEY,
        scenario_name TEXT,
        indexation_rate REAL,
        van_tnd REAL,
        tri_percent REAL,
        roi_percent REAL,
        payback_years REAL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS aquatic_gain (
        dam_id INTEGER PRIMARY KEY,
        gain_percent REAL,
        gain_kwh REAL,
        FOREIGN KEY (dam_id) REFERENCES dams(id)
    )""")

    # --- Dams ---
    dams = [
        (1, "Sidi Salem", 1703, 5095, 4300, 2200000, "--", 15.0,
         "Dépassement du seuil recommandé (15 %). Une étude d'impact supplémentaire serait nécessaire.", 92489),
        (2, "Sidi El Barrak", 1646, 5066, 2734, 2250000, "--", 15.0,
         "Dépassement du seuil recommandé (15 %). Une étude d'impact supplémentaire serait nécessaire.", 92489),
        (3, "Bouhertma", 1696, 2908, 880, 2350000, "--", 15.0,
         "Dépassement du seuil recommandé (15 %). Une étude d'impact supplémentaire serait nécessaire.", 92489),
        (4, "Sejnane", 1660, 4919, 732, 2350000, "AEP", 5.0,
         "Dépassement du seuil recommandé (5 %). Usage AEP prioritaire : une étude approfondie de la qualité de l'eau est impérative.", 92489),
        (5, "Sidi Saad", 1780, 5863, 1104, 2300000, "Ramsar", 5.0,
         "Site Ramsar : taux de couverture très faible requis. Une étude d'impact environnementale est obligatoire.", 92489),
    ]
    c.executemany("INSERT OR REPLACE INTO dams VALUES (?,?,?,?,?,?,?,?,?,?)", dams)

# --- Constants ---
    # MODIFIÉ : J1 = 0.307 TND/kWh ; J7 = 0,476 tCO₂/MWh = 0,000476 tCO₂/kWh
    constants = [
        ("J1", 0.307, "Prix de vente initial (TND/kWh)"),
        ("J2", 0.05, "Indexation annuelle"),
        ("J3", 0.004, "Dégradation annuelle"),
        ("J4", 0.02, "Taux OPEX"),
        ("J5", 0.10, "Taux actualisation"),
        ("J6", 25, "Durée de vie (ans)"),
        ("J7", 0.000476, "Facteur CO₂ évité (t/kWh) - réseau tunisien 0,476 tCO₂/MWh"),
        ("J8", 0.0000358, "Facteur CO₂ FPV (t/kWh)"),
    ]
    c.executemany("INSERT OR REPLACE INTO constants VALUES (?,?,?)", constants)

    # --- Evaporation data (all 5 dams) ---
    evap_data = [
        # Sidi Saad (id=5)
        (5,1,"Janvier",11.1,66.2,2.11,2.74,2.327,31,6672,4670),
        (5,2,"Février",11.8,61.5,2.21,3.62,2.987,28,7736,5415),
        (5,3,"Mars",14.8,59.0,2.09,4.82,4.006,31,11486,8040),
        (5,4,"Avril",18.0,57.2,1.99,6.04,5.166,30,14334,10034),
        (5,5,"Mai",22.1,50.4,2.01,6.93,6.593,31,18902,13231),
        (5,6,"Juin",26.8,44.2,1.95,7.67,8.061,30,22367,15656),
        (5,7,"Juillet",30.1,41.6,1.83,7.63,8.543,31,24493,17145),
        (5,8,"Août",29.5,46.1,1.63,6.73,7.405,31,21231,14861),
        (5,9,"Septembre",25.3,59.6,1.56,5.44,5.405,30,14996,10497),
        (5,10,"Octobre",21.5,64.2,1.49,4.13,3.929,31,11263,7884),
        (5,11,"Novembre",16.0,64.8,1.81,2.89,2.769,30,7683,5378),
        (5,12,"Décembre",12.2,67.1,2.06,2.41,2.211,31,6337,4436),
        # Sidi Salem (id=1)
        (1,1,"Janvier",10.7,78.1,2.63,2.38,1.826,31,5236,3665),
        (1,2,"Février",10.9,76.2,2.63,3.20,2.281,28,5907,4135),
        (1,3,"Mars",13.4,73.9,2.46,4.44,3.185,31,9133,6393),
        (1,4,"Avril",16.4,70.8,2.07,5.62,4.249,30,11791,8254),
        (1,5,"Mai",20.2,63.9,2.016,6.46,5.490,31,15742,11019),
        (1,6,"Juin",25.1,54.7,1.98,7.44,7.205,30,19990,13993),
        (1,7,"Juillet",28.2,52.3,2.05,7.51,7.848,31,22500,15750),
        (1,8,"Août",28.0,55.1,1.82,6.68,6.944,31,19911,13937),
        (1,9,"Septembre",24.3,66.2,1.81,5.14,4.944,30,13718,9603),
        (1,10,"Octobre",20.8,70.1,1.66,3.84,3.542,31,10156,7109),
        (1,11,"Novembre",15.5,73.8,2.14,2.58,2.343,30,6502,4552),
        (1,12,"Décembre",11.8,78.0,2.47,2.07,1.739,31,4985,3490),
        # Sidi El Barrak (id=2)
        (2,1,"Janvier",11.5,78.2,3.98,2.12,1.879,31,5386,3770),
        (2,2,"Février",11.6,77.1,4.07,2.99,2.301,28,5958,4170),
        (2,3,"Mars",13.9,74.2,4.05,4.24,3.214,31,9216,6451),
        (2,4,"Avril",16.6,72.3,3.76,5.42,4.201,30,11657,8160),
        (2,5,"Mai",19.8,68.0,3.72,6.46,5.467,31,15674,10972),
        (2,6,"Juin",24.0,63.2,3.31,7.47,7.002,30,19427,13599),
        (2,7,"Juillet",26.9,61.2,3.32,7.50,7.650,31,21935,15354),
        (2,8,"Août",27.0,63.6,3.11,6.54,6.796,31,19486,13640),
        (2,9,"Septembre",24.0,70.7,3.01,4.93,4.871,30,13517,9462),
        (2,10,"Octobre",20.9,72.4,2.95,3.63,3.623,31,10388,7271),
        (2,11,"Novembre",16.1,74.4,3.42,2.34,2.458,30,6820,4774),
        (2,12,"Décembre",12.7,77.8,3.78,1.84,1.846,31,5294,3706),
        # Bouhertma (id=3)
        (3,1,"Janvier",10.4,78.4,3.0,2.12,1.068,31,3062,2143),
        (3,2,"Février",10.8,77.3,3.09,2.99,1.240,28,3211,2248),
        (3,3,"Mars",13.2,75.5,3.05,4.24,1.593,31,4567,3197),
        (3,4,"Avril",16.3,72.7,2.95,5.42,2.055,30,5702,3992),
        (3,5,"Mai",20.3,65.1,3.09,6.46,2.916,31,8359,5851),
        (3,6,"Juin",25.4,54.7,3.08,7.47,4.153,30,11524,8067),
        (3,7,"Juillet",28.7,51.3,3.16,7.50,4.781,31,13708,9595),
        (3,8,"Août",28.3,54.0,2.9,6.54,4.202,31,12047,8433),
        (3,9,"Septembre",24.4,65.1,2.73,4.93,2.838,30,7875,5513),
        (3,10,"Octobre",20.7,68.5,2.5,3.63,2.097,31,6013,4209),
        (3,11,"Novembre",15.1,74.1,2.77,2.34,1.434,30,3978,2784),
        (3,12,"Décembre",11.4,78.5,2.94,1.84,1.060,31,3040,2128),
        # Sejnane (id=4)
        (4,1,"Janvier",10.9,83.6,3.28,2.12,1.563,31,4479,3136),
        (4,2,"Février",11.1,80.7,3.34,2.97,2.060,28,5335,3735),
        (4,3,"Mars",13.6,76.6,3.32,4.26,3.045,31,8731,6112),
        (4,4,"Avril",16.6,73.7,3.05,5.49,4.136,30,11476,8033),
        (4,5,"Mai",20.2,67.2,3.24,6.50,5.548,31,15908,11135),
        (4,6,"Juin",24.6,61.6,3.04,7.50,7.161,30,19870,13909),
        (4,7,"Juillet",27.4,60.0,3.07,7.53,7.756,31,22237,15566),
        (4,8,"Août",27.4,63.4,2.69,6.60,6.773,31,19420,13594),
        (4,9,"Septembre",24.0,71.9,2.65,5.00,4.777,30,13254,9278),
        (4,10,"Octobre",20.7,75.8,2.4,3.65,3.352,31,9610,6727),
        (4,11,"Novembre",15.8,79.5,2.77,2.38,2.131,30,5913,4139),
        (4,12,"Décembre",12.0,83.4,2.99,1.87,1.507,31,4320,3024),
    ]
    c.executemany("""INSERT OR REPLACE INTO evaporation_monthly
        (dam_id, month, month_name, temp_c, hr_percent, wind_ms, rs_kwh_m2_day, e_mm_day, days, volume_without_fpv, volume_with_fpv)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""", evap_data)

    # --- Thermal data: Sidi Saad (exact from PVsyst) ---
    thermal_sidi_saad = [
        (5,1,"Janvier",11.1,2.11,31,112.1,10,361.6,254.5,23.83,16.01,1788625,1850253,61628,3.45),
        (5,2,"Février",11.8,2.21,28,123.9,11,402.3,283.1,25.96,17.17,2167160,2253746,86586,3.99),
        (5,3,"Mars",14.8,2.09,31,168.6,12,453.2,319.0,30.75,20.97,2938135,3065732,127597,4.34),
        (5,4,"Avril",18.0,1.99,30,192.4,13,493.3,347.2,35.36,24.82,3312073,3461347,149274,4.51),
        (5,5,"Mai",22.1,2.01,31,217.4,14,500.9,352.5,39.73,29.00,3685068,3862201,177133,4.81),
        (5,6,"Juin",26.8,1.95,30,227.3,15,505.1,355.5,44.57,33.83,3782472,3981709,199237,5.27),
        (5,7,"Juillet",30.1,1.83,31,235.6,14,542.9,382.1,49.20,37.80,3860227,4070896,210669,5.46),
        (5,8,"Août",29.5,1.63,31,217.7,14,501.6,353.0,47.15,36.85,3584438,3766958,182520,5.09),
        (5,9,"Septembre",25.3,1.56,30,180.5,12,501.4,352.9,42.94,32.73,3038337,3184265,145928,4.80),
        (5,10,"Octobre",21.5,1.49,31,151.9,11,445.5,313.5,37.18,28.18,2594638,2701714,107076,4.13),
        (5,11,"Novembre",16.0,1.81,30,110.5,10,368.3,259.2,28.96,21.24,1886084,1948662,62578,3.32),
        (5,12,"Décembre",12.2,2.06,31,101.1,10,326.1,229.5,23.68,16.66,1699436,1755352,55916,3.29),
    ]
    c.executemany("""INSERT OR REPLACE INTO thermal_monthly
        (dam_id, month, month_name, temp_c, wind_ms, days, ginc_w_m2_month, nb_h_sun, ginc_w_m2, alpha_ginc_1_eta,
         tcell_terre, tcell_float, egrid_terre_kwh, egrid_float_kwh, gain_kwh, gain_percent)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", thermal_sidi_saad)

    # --- PLACEHOLDER thermal data for other dams (scaled from Sidi Saad by productible ratio) ---
    dam_factors = {1: 1703/1780, 2: 1646/1780, 3: 1696/1780, 4: 1660/1780}

    for dam_id, factor in dam_factors.items():
        for row in thermal_sidi_saad:
            _, _, month_name, temp_c, wind_ms, days, ginc_w_m2_month, nb_h_sun, ginc_w_m2, alpha_ginc_1_eta, tcell_terre, tcell_float, egrid_terre_kwh, egrid_float_kwh, gain_kwh, gain_percent = row
            temp_adj = -2.0 if dam_id in [1,2,3,4] else 0
            new_row = (
                dam_id, row[1], month_name,
                temp_c + temp_adj, wind_ms, days,
                ginc_w_m2_month * factor, nb_h_sun, ginc_w_m2 * factor,
                alpha_ginc_1_eta,
                tcell_terre + temp_adj * 0.8,
                tcell_float + temp_adj * 0.5,
                egrid_terre_kwh * factor,
                egrid_float_kwh * factor * 1.02,
                gain_kwh * factor,
                gain_percent * 1.05
            )
            c.execute("""INSERT OR REPLACE INTO thermal_monthly
        (dam_id, month, month_name, temp_c, wind_ms, days, ginc_w_m2_month, nb_h_sun, ginc_w_m2, alpha_ginc_1_eta,
         tcell_terre, tcell_float, egrid_terre_kwh, egrid_float_kwh, gain_kwh, gain_percent)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", new_row)

    # --- Aquatic gain data (from thermal_monthly aggregated) ---
    aquatic_data = [
        (1, 3.45, 782300),  # Sidi Salem
        (2, 3.45, 762900),  # Sidi El Barrak
        (3, 3.15, 532900),  # Bouhertma
        (4, 3.15, 688300),  # Sejnane
        (5, 4.28, 1566142), # Sidi Saad
    ]
    c.executemany("INSERT OR REPLACE INTO aquatic_gain VALUES (?,?,?)", aquatic_data)

    # --- Economic scenarios ---
    # MODIFIÉ : recalculés avec J1 = 0.307 TND/kWh
    scenarios = [
        (1, "Conservateur (2%)", 0.02, 26153334.77, 15.36, 418.0, 9),
        (2, "Base (5%)", 0.05, 56535297.29, 19.16, 743.0, 7),
        (3, "Optimiste (8%)", 0.08, 101277061.26, 22.78, 1267.0, 6),
    ]
    c.executemany("INSERT OR REPLACE INTO economic_scenarios VALUES (?,?,?,?,?,?,?)", scenarios)

    conn.commit()
    conn.close()
    print("Base de données initialisée avec succès.")
    print("   -> 5 barrages, 5 constantes (J1=0.307), 60 lignes évaporation, 60 lignes thermiques, 5 gains aquatiques, 3 scénarios.")

if __name__ == "__main__":
    init_db()