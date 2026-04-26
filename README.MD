# 🦆 MALLARD

### Local Data Warehouse · Data Refiner Edition

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![DuckDB](https://img.shields.io/badge/DuckDB-1.2.2-yellow?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.45.1-red?style=flat-square&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square&logo=windows)

> Drop your CSV, Excel, Parquet, or JSON. Let the duck do the rest.

MALLARD is a **100% local, zero-server data tool** built on DuckDB + Streamlit. Upload messy datasets, auto-clean them, explore with interactive charts, run custom SQL, and export the refined result — all without touching the cloud.

<p align="center">
  <img src="assets/welcome.png" width="700"/>
  <img src="assets/dashboard.png" width="700"/>
</p>

---

## 🎬 Demo

<p align="center">
  <img src="assets/demo.gif" width="700" alt="MALLARD demo"/>
</p>

---

## ✨ Features

- **Multi-format Ingestion** — CSV, Excel (.xlsx/.xls), Parquet, JSON.
- **Zero-Pandas Memory Footprint** — Uses DuckDB native SQL pushdowns to process larger-than-RAM datasets without Out-Of-Memory (OOM) crashes.
- **Auto Deep Clean** — Deduplication, empty column removal, and statistical type healing (no hardcoded logic).
- **Smart Summary** — Automated insights and missing-value detection processed instantly inside the DB engine.
- **Analytics Explorer** — Uses smart SQL sampling and native aggregation before rendering charts to keep the browser lightning fast.
- **Custom SQL** — Run any DuckDB query directly against your tables.
- **Direct-to-Disk Export** — Ultra-fast downloads (CSV, Parquet, JSON) bypassing Python RAM using DuckDB's native `COPY` command.
- **100% Local** — Data never leaves your machine, no cloud upload required.
- **Standalone .exe** — Distributable to Windows users with no Python setup needed.

---

## 🚀 Quick Start

### Option 1 — Run from source

```bash
# 1. Clone repo
git clone https://github.com/KMoex-HZ/mallard.git
cd mallard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run mallard.py
```

### Option 2 — Windows .exe (no Python needed)

1. Download `MALLARD.zip` from [Releases](../../releases)
2. Extract the zip
3. Double-click `MALLARD.exe`
4. Browser opens automatically at `http://localhost:8501`

---

## 📦 Requirements

```
streamlit==1.45.1
duckdb==1.2.2
pandas==2.2.3
plotly==6.0.1
openpyxl==3.1.5
pyarrow==19.0.1
xlrd==2.0.1
psutil==6.1.1
```

Python 3.10+ recommended.

---

## 🛠️ Build .exe from source

```bash
pip install pyinstaller pyinstaller-hooks-contrib
python setup_exe.py
```

Output: `dist/MALLARD/MALLARD.exe`  
Distribute the entire `dist/MALLARD/` folder as a zip.

---

## 🧹 How Deep Clean works

| Step                  | What it does                                                      |
| --------------------- | ----------------------------------------------------------------- |
| Deduplication         | Removes exact duplicate rows via native SQL `DISTINCT`            |
| Empty column removal  | Drops columns with zero non-null values instantly via metadata count |
| Smart Numeric Healing | Uses statistical execution (`TRY_CAST`) to detect and convert dirty VARCHAR numbers into DOUBLE, bypassing hardcoded column names |
| Wide-format detection | Auto-melts date-header pivot tables into long format              |

---

## 📁 Project Structure

```
mallard/
├── mallard.py          # Main Streamlit app
├── launcher.py         # Entry point for .exe build
├── setup_exe.py        # PyInstaller build script
├── requirements.txt
└── data/               # Auto-created, drop files here for auto-ingestion
```

---

## 🦆 Why MALLARD?

Most data tools are either too heavy (full BI platforms) or too barebones (just a CSV viewer). MALLARD lives in the middle — a local warehouse that's fast, opinionated, and actually fixes your data before you analyze it. 

By leveraging DuckDB's in-process OLAP engine, it allows you to process datasets that would normally crash a standard pandas/Streamlit app.

No Tableau license. No cloud upload. Just a duck and DuckDB.

---
## Author

Khairunnisa Maharani

## License

MIT
