#!/bin/bash
echo "Initialisation de la base de données..."
python3 init_db.py
echo "Lancement de l'application FPV Tunisia..."
streamlit run app.py
