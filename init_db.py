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
    
    # Clear tables for fresh data
    c.execute("DELETE FROM thermal_monthly")

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
    
    c.execute("DELETE FROM evaporation_monthly")
    c.execute("DELETE FROM thermal_monthly")

# --- Constants ---
    # MODIFIÉ : J1 = 0.307 TND/kWh ; J7 = 476 kgCO₂/MWh ; J8 = 35.8 kgCO₂/MWh
    constants = [
        ("J1", 0.307, "Prix de vente initial (TND/kWh)"),
        ("J2", 0.05, "Indexation annuelle"),
        ("J3", 0.004, "Degradation annuelle"),
        ("J4", 0.02, "Taux OPEX"),
        ("J5", 0.10, "Taux actualisation"),
        ("J6", 25, "Duree de vie (ans)"),
        ("J7", 476.0, "Facteur CO2 evite (kg/MWh) - reseau tunisien 0,476 tCO2/MWh"),
        ("J8", 35.8, "Facteur CO2 FPV (kg/MWh) - 0,0358 tCO2/MWh"),
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

    # --- Thermal data: Monthly aquatic gain percentages per dam ---
# Sidi Saad (id=5) - gain_percent values from the new data
    thermal_sidi_saad = [
        (5,1,"Janvier",11.1,2.11,31,112.1,10,361.6,254.5,23.83,16.01,1788625,1850253,61628,3.45),
        (5,2,"Février",11.8,2.21,28,123.9,11,402.3,283.1,25.96,17.17,2167160,2253746,86586,4.00),
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

    # --- Thermal data for other dams with NEW monthly gain_percent values ---
    thermal_sidi_salem = [
        (1,1,"Janvier",10.7,2.63,31,95.7,308.71,217.27,21.56,14.58,6.99,1788625*0.957,1850253*0.957,61628*0.957,3.27),
        (1,2,"Février",10.9,2.63,28,109.1,354.22,249.30,23.37,15.35,8.02,2167160*0.957,2253746*0.957,86586*0.957,5.09),
        (1,3,"Mars",13.4,2.46,31,156.1,419.62,295.33,28.17,18.80,9.37,2938135*0.957,3065732*0.957,127597*0.957,5.56),
        (1,4,"Avril",16.4,2.07,30,179.1,459.23,323.21,32.56,22.67,9.89,3312073*0.957,3461347*0.957,149274*0.957,5.73),
        (1,5,"Mai",20.2,2.02,31,202.9,467.51,329.03,36.65,26.64,10.02,3685068*0.957,3862201*0.957,177133*0.957,6.02),
        (1,6,"Juin",25.1,1.98,30,221.7,492.67,346.74,42.44,31.92,10.52,3782472*0.957,3981709*0.957,199237*0.957,6.30),
        (1,7,"Juillet",28.2,2.05,31,233.6,538.25,378.82,47.14,35.57,11.57,3860227*0.957,4070896*0.957,210669*0.957,6.64),
        (1,8,"Août",28.0,1.82,31,216.8,499.54,351.58,45.58,35.09,10.48,3584438*0.957,3766958*0.957,182520*0.957,6.45),
        (1,9,"Septembre",24.3,1.81,30,170.8,474.44,333.91,41.00,31.05,9.95,3038337*0.957,3184265*0.957,145928*0.957,6.02),
        (1,10,"Octobre",20.8,1.66,31,142.4,417.60,293.90,35.50,26.89,8.61,2594638*0.957,2701714*0.957,107076*0.957,5.50),
        (1,11,"Novembre",15.5,2.14,30,98.5,328.33,231.08,27.05,19.93,7.12,1886084*0.957,1948662*0.957,62578*0.957,4.59),
        (1,12,"Décembre",11.8,2.47,31,84.5,272.58,191.84,21.39,15.30,6.09,1699436*0.957,1755352*0.957,55916*0.957,4.46),
    ]
    c.executemany("""INSERT OR REPLACE INTO thermal_monthly
        (dam_id, month, month_name, temp_c, wind_ms, days, ginc_w_m2_month, nb_h_sun, ginc_w_m2, alpha_ginc_1_eta,
         tcell_terre, tcell_float, egrid_terre_kwh, egrid_float_kwh, gain_kwh, gain_percent)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", thermal_sidi_salem)

    # --- Thermal data: Sidi El Barrak (id=2) - NEW monthly gain_percent values ---
    thermal_sidi_barrak = [
        (2,1,"Janvier",11.5,3.98,31,65.8,212.26,149.39,18.97,13.73,5.23,1788625*0.923,1850253*0.923,61628*0.923,3.35),
        (2,2,"Février",11.6,4.07,28,83.7,271.75,191.26,21.16,14.43,6.73,2167160*0.923,2253746*0.923,86586*0.923,3.95),
        (2,3,"Mars",13.9,4.05,31,131.5,353.50,248.79,26.34,17.59,8.75,2938135*0.923,3065732*0.923,127597*0.923,4.63),
        (2,4,"Avril",16.6,3.76,30,162.6,416.92,293.43,31.27,21.11,10.16,3312073*0.923,3461347*0.923,149274*0.923,4.97),
        (2,5,"Mai",19.8,3.72,31,200.3,461.52,324.82,36.04,24.82,11.23,3685068*0.923,3862201*0.923,177133*0.923,5.26),
        (2,6,"Juin",24.0,3.31,30,224.1,498.00,350.49,41.52,29.70,11.82,3782472*0.923,3981709*0.923,199237*0.923,5.39),
        (2,7,"Juillet",26.9,3.32,31,232.4,535.48,376.87,45.74,33.02,12.72,3860227*0.923,4070896*0.923,210669*0.923,5.64),
        (2,8,"Août",27.0,3.11,31,202.9,467.51,329.03,43.45,32.49,10.96,3584438*0.923,3766958*0.923,182520*0.923,5.33),
        (2,9,"Septembre",24.0,3.01,30,147.9,410.83,289.14,38.46,28.89,9.56,3038337*0.923,3184265*0.923,145928*0.923,4.92),
        (2,10,"Octobre",20.9,2.95,31,112.4,329.62,231.99,32.50,24.86,7.64,2594638*0.923,2701714*0.923,107076*0.923,4.38),
        (2,11,"Novembre",16.1,3.42,30,70.3,234.33,164.92,24.35,18.74,5.60,1886084*0.923,1948662*0.923,62578*0.923,3.29),
        (2,12,"Décembre",12.7,3.78,31,57.1,184.19,129.64,19.18,14.69,4.49,1699436*0.923,1755352*0.923,55916*0.923,3.25),
    ]
    c.executemany("""INSERT OR REPLACE INTO thermal_monthly
        (dam_id, month, month_name, temp_c, wind_ms, days, ginc_w_m2_month, nb_h_sun, ginc_w_m2, alpha_ginc_1_eta,
         tcell_terre, tcell_float, egrid_terre_kwh, egrid_float_kwh, gain_kwh, gain_percent)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", thermal_sidi_barrak)

    # --- Thermal data: Bouhertma (id=3) - NEW monthly gain_percent values ---
    thermal_bouhertma = [
        (3,1,"Janvier",10.4,3.0,31,85.0,274.19,192.98,20.05,13.67,6.38,1788625*0.902,1850253*0.902,61628*0.902,3.47),
        (3,2,"Février",10.8,3.09,28,100.0,324.68,228.51,22.23,14.63,7.60,2167160*0.902,2253746*0.902,86586*0.902,3.85),
        (3,3,"Mars",13.2,3.05,31,149.1,400.81,282.09,27.30,17.95,9.36,2938135*0.902,3065732*0.902,127597*0.902,4.49),
        (3,4,"Avril",16.3,2.95,30,173.0,443.59,312.20,31.91,21.63,10.28,3312073*0.902,3461347*0.902,149274*0.902,4.57),
        (3,5,"Mai",20.3,3.09,31,203.1,467.97,329.36,36.77,25.82,10.95,3685068*0.902,3862201*0.902,177133*0.902,5.13),
        (3,6,"Juin",25.4,3.08,30,222.6,494.67,348.15,42.81,31.24,11.57,3782472*0.902,3981709*0.902,199237*0.902,5.52),
        (3,7,"Juillet",28.7,3.16,31,233.3,537.56,378.33,47.62,34.98,12.64,3860227*0.902,4070896*0.902,210669*0.902,5.78),
        (3,8,"Août",28.3,2.9,31,211.8,488.02,343.47,45.47,34.20,11.27,3584438*0.902,3766958*0.902,182520*0.902,5.49),
        (3,9,"Septembre",24.4,2.73,30,163.5,454.17,319.64,40.38,30.02,10.36,3038337*0.902,3184265*0.902,145928*0.902,4.99),
        (3,10,"Octobre",20.7,2.5,31,132.5,388.56,273.47,34.37,25.67,8.70,2594638*0.902,2701714*0.902,107076*0.902,4.46),
        (3,11,"Novembre",15.1,2.77,30,87.6,292.00,205.51,25.38,18.70,6.68,1886084*0.902,1948662*0.902,62578*0.902,3.34),
        (3,12,"Décembre",11.4,2.94,31,74.9,241.61,170.05,19.90,14.31,5.60,1699436*0.902,1755352*0.902,55916*0.902,3.03),
    ]
    c.executemany("""INSERT OR REPLACE INTO thermal_monthly
        (dam_id, month, month_name, temp_c, wind_ms, days, ginc_w_m2_month, nb_h_sun, ginc_w_m2, alpha_ginc_1_eta,
         tcell_terre, tcell_float, egrid_terre_kwh, egrid_float_kwh, gain_kwh, gain_percent)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", thermal_bouhertma)

    # --- Thermal data: Sejnane (id=4) - NEW monthly gain_percent values ---
    thermal_sejnane = [
        (4,1,"Janvier",10.9,3.28,31,65.8,212.26,149.39,18.37,13.34,5.03,1788625*0.932,1850253*0.932,61628*0.932,3.20),
        (4,2,"Février",11.1,3.34,28,83.1,269.81,189.89,20.59,14.18,6.42,2167160*0.932,2253746*0.932,86586*0.932,4.12),
        (4,3,"Mars",13.6,3.32,31,132.1,355.11,249.92,26.10,17.66,8.44,2938135*0.932,3065732*0.932,127597*0.932,4.36),
        (4,4,"Avril",16.6,3.05,30,164.6,422.05,297.04,31.45,21.60,9.85,3312073*0.932,3461347*0.932,149274*0.932,4.89),
        (4,5,"Mai",20.2,3.24,31,201.6,464.52,326.93,36.55,25.57,10.98,3685068*0.932,3862201*0.932,177133*0.932,5.18),
        (4,6,"Juin",24.6,3.04,30,225.0,500.00,351.90,42.20,30.53,11.66,3782472*0.932,3981709*0.932,199237*0.932,5.29),
        (4,7,"Juillet",27.4,3.07,31,233.3,537.56,378.33,46.32,33.75,12.56,3860227*0.932,4070896*0.932,210669*0.932,5.70),
        (4,8,"Août",27.4,2.69,31,204.5,471.20,331.63,43.98,33.27,10.71,3584438*0.932,3766958*0.932,182520*0.932,5.53),
        (4,9,"Septembre",24.0,2.65,30,149.9,416.39,293.05,38.65,29.21,9.44,3038337*0.932,3184265*0.932,145928*0.932,4.78),
        (4,10,"Octobre",20.7,2.4,31,113.1,331.67,233.43,32.37,25.01,7.36,2594638*0.932,2701714*0.932,107076*0.932,4.15),
        (4,11,"Novembre",15.8,2.77,30,71.4,238.00,167.50,24.18,18.73,5.44,1886084*0.932,1948662*0.932,62578*0.932,3.23),
        (4,12,"Décembre",12.0,2.99,31,58.0,187.10,131.68,18.58,14.23,4.35,1699436*0.932,1755352*0.932,55916*0.932,2.93),
    ]
    c.executemany("""INSERT OR REPLACE INTO thermal_monthly
        (dam_id, month, month_name, temp_c, wind_ms, days, ginc_w_m2_month, nb_h_sun, ginc_w_m2, alpha_ginc_1_eta,
         tcell_terre, tcell_float, egrid_terre_kwh, egrid_float_kwh, gain_kwh, gain_percent)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", thermal_sejnane)

    # --- Aquatic gain data (average gain_percent from monthly values) ---
    aquatic_data = [
        (1, 6.15, 782300),  # Sidi Salem
        (2, 4.82, 762900),  # Sidi El Barrak
        (3, 4.78, 532900),  # Bouhertma
        (4, 4.75, 688300),  # Sejnane
        (5, 4.56, 1566142), # Sidi Saad
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