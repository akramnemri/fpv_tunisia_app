Streamlit Community Cloud Deployment
====================================

1. Push this repository to GitHub
2. Go to https://streamlit.io/cloud
3. Connect your GitHub account
4. Select the FPV-Tunisia repository
5. Set:
   - Main file path: app.py
   - Python version: 3.11
6. Click "Deploy"

The app will automatically:
- Install dependencies from requirements.txt
- Run init_db.py to create the database
- Launch the Streamlit app

No installation required for users - just a web browser!