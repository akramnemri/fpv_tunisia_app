"""Configuration globale et accès base de données."""
import os
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "dams.db")

@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def load_constants(conn):
    df = pd.read_sql("SELECT * FROM constants", conn)
    return {row['key']: row['value'] for _, row in df.iterrows()}

def load_dams(conn):
    return pd.read_sql("SELECT * FROM dams ORDER BY id", conn)

def load_evap(conn, dam_id):
    return pd.read_sql(
        "SELECT * FROM evaporation_monthly WHERE dam_id=? ORDER BY month",
        conn, params=(dam_id,)
    )

def load_thermal(conn, dam_id):
    return pd.read_sql(
        "SELECT * FROM thermal_monthly WHERE dam_id=? ORDER BY month",
        conn, params=(dam_id,)
    )

def load_scenarios(conn):
    return pd.read_sql("SELECT * FROM economic_scenarios ORDER BY id", conn)

def get_aquatic_gain(dam_id: int) -> dict:
    """Récupère le gain thermique aquatique pour un barrage (base 20 MWc)."""
    import sqlite3
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT gain_percent, gain_kwh FROM aquatic_gain WHERE dam_id=?", (dam_id,))
    row = c.fetchone()
    if row:
        return {"gain_percent": row[0], "gain_kwh": row[1]}
    return {"gain_percent": 0.0, "gain_kwh": 0}
