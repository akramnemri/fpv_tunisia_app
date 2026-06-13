# FPV Tunisia App

A Streamlit-based decision support tool for analyzing Floating Photovoltaic (FPV) systems on Tunisian reservoirs. This application addresses Tunisia's dual challenges of energy transition and water preservation through floating solar installations.

## Overview

Tunisia faces two strategic challenges:
- **Energy Security**: Heavy reliance on fossil fuels (96% of electricity production), with a national target of 35% renewable energy by 2030
- **Water Scarcity**: Severe water stress with evaporation losses reaching up to 17% of annual inflows in some reservoirs

Floating Photovoltaics (FPV) offer an integrated solution by:
- Generating clean electricity without land-use conflicts
- Reducing water evaporation through shading
- Improving panel efficiency through water-based cooling (5-15% gain)

## Features

- **Site Analysis**: Evaluate potential reservoir sites for FPV deployment with constraint types (Ramsar, AEP)
- **Energy Modeling**: Simulate solar production with thermal performance comparison (ground vs floating)
- **Water Savings Calculation**: Estimate monthly evaporation reduction using Penman-Monteith methodology
- **Economic Assessment**: Calculate LCOE, VAN, TRI, ROI, and payback periods across scenarios
- **Multi-Dam Comparison**: Compare all 5 supported reservoirs side-by-side

## Supported Reservoir Sites

| Barrage | Productible (MWc) | Économie eau (m³/MWc) | Surface (ha) | Contrainte |
|---------|-------------------|----------------------|--------------|------------|
| Sidi Salem | 1,703 | 5,095 | 4,300 | -- |
| Sidi El Barrak | 1,646 | 5,066 | 2,734 | -- |
| Bouhertma | 1,696 | 2,908 | 880 | -- |
| Sejnane | 1,660 | 4,919 | 732 | AEP |
| Sidi Saad | 1,780 | 5,863 | 1,104 | Ramsar |

## Prerequisites

- Python 3.13 or higher
- SQLite3 (included with Python)

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Initialize the database:
   ```
   python init_db.py
   ```

## Installation

```
pip install streamlit>=1.28.0 pandas>=2.0.0 numpy>=1.24.0 numpy-financial>=1.0.0 plotly>=5.18.0
```

## Running the Application

### Quick Start (Windows)
```
run.bat
```

### Manual Start
```
streamlit run app.py
```

## Project Structure

```
fpv_tunisia_app/
├── app.py                 # Main Streamlit application
├── init_db.py             # Database initialization script
├── requirements.txt       # Python dependencies
├── run.bat                # Windows launcher
├── run.sh                 # Unix launcher
├── LICENSE                # MIT License
├── README.md              # This file
├── Rapport Mayssa (1).docx # Technical documentation
├── .gitignore             # Git ignore rules
└── src/
    ├── __init__.py
    ├── config.py          # Database connection & constants loading
    ├── models.py          # Pydantic models (DamProfile, EconomicConstants, ProjectInputs)
    ├── engine.py          # Core computation logic
    ├── charts.py          # Plotly chart utilities
    └── tabs/
        ├── __init__.py
        ├── simulation_tab.py
        ├── evaporation_tab.py
        ├── thermal_tab.py
        ├── scenarios_tab.py
        └── comparison_tab.py
│     └── ranking_tab.py
```

## Database Schema

The application uses SQLite with the following tables:
- `dams`: Barrage characteristics (productible power, water savings, constraints)
- `constants`: Economic parameters (tariff, degradation, OPEX, CO₂ factors)
- `evaporation_monthly`: Monthly evaporation data per dam
- `thermal_monthly`: Thermal performance data (temperature, energy gain)
- `economic_scenarios`: Pre-calculated economic scenarios (conservative, base, optimistic)

## Architecture

The application follows a modular architecture:
- **config.py**: Database connection and data loading
- **models.py**: Pydantic models for type safety
- **engine.py**: Core project computation logic
- **charts.py**: Reusable chart components
- **tabs/**: Streamlit UI tabs for each analysis section

## Technical Details

### Economic Parameters
- Initial tariff: 0.307 TND/kWh (STEG 2025)
- CAPEX unitaire fixe: 2,300,000 TND/MWc
- Annual degradation: 0.4%
- OPEX rate: 2%
- Discount rate: 10%
- Project lifetime: 25 years
- CO₂ avoided factor: 0.476 t/MWh (Tunisian grid factor)

### Constraints
- **AEP (Alimentation En Eau Potable)**: Drinking water supply - requires water quality studies
- **Ramsar**: Wetland site - strict coverage limits required
- Coverage thresholds: 5% (Sejnane, Sidi Saad), 15% (others)

## License

MIT License - see [LICENSE](LICENSE) for details.