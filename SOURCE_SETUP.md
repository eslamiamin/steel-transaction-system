# Source package

This package combines the V1.3 UI patch with the V1 database module. The SQL Server host is now supplied through STEEL_SERVER.

Windows CMD:
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
set STEEL_SERVER=YOUR_SERVER\INSTANCE
set STEEL_DB=SteelTransaction_POC
python -m streamlit run app_v1.py
```
Requires ODBC Driver 17 and an existing compatible database with the V1 migration applied. Not a clean database bootstrap. Dependency versions are not pinned. Syntax checked only; no live database test. Review documentation and source before public release.
