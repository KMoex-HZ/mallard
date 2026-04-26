import streamlit as st
import duckdb
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from io import BytesIO
import tempfile
import os
import json

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="MALLARD", page_icon="🦆", layout="wide")

DATA_DIR = Path("data")
DB_PATH  = "mallard.duckdb"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Sora:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.stApp { background-color: #080c14; color: #dce4f0; }

section[data-testid="stSidebar"] {
    background-color: #0d1220;
    border-right: 1px solid #1e2a40;
}
section[data-testid="stSidebar"] * { color: #a8b8d0 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #dce4f0 !important; }

[data-testid="metric-container"] {
    background: linear-gradient(135deg, #0d1828 0%, #111e30 100%);
    border: 1px solid #1e3050;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}
[data-testid="metric-container"] label {
    color: #5a7a9a !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="metric-value"] {
    color: #e8f0ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.6rem !important;
}

.stButton > button {
    background: linear-gradient(135deg, #1a4fd6, #2563eb);
    color: white !important;
    border: none;
    border-radius: 8px;
    padding: 9px 22px;
    font-weight: 600;
    font-family: 'Sora', sans-serif;
    letter-spacing: 0.02em;
    transition: all 0.2s;
    box-shadow: 0 2px 12px rgba(37,99,235,0.3);
    width: 100%;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1e40af, #1d4ed8);
    box-shadow: 0 4px 20px rgba(37,99,235,0.5);
    transform: translateY(-1px);
}

.summary-box {
    background: linear-gradient(135deg, #0d1828 0%, #0f1f35 100%);
    border-left: 3px solid #2563eb;
    border-radius: 10px;
    padding: 22px 26px;
    margin: 12px 0;
    line-height: 1.9;
    color: #b8cce0;
    font-size: 0.95rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}

.clean-box {
    background: linear-gradient(135deg, #0a1f12 0%, #0d2a18 100%);
    border-left: 3px solid #16a34a;
    border-radius: 10px;
    padding: 20px 24px;
    margin: 10px 0;
    line-height: 1.9;
    color: #a0d4b0;
    font-size: 0.9rem;
}
.clean-box table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
    font-size: 0.83rem;
}
.clean-box th {
    text-align: left;
    color: #4ade80 !important;
    border-bottom: 1px solid #1a4a2a;
    padding: 5px 10px;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
}
.clean-box td {
    padding: 4px 10px;
    border-bottom: 1px solid #0f2a18;
    color: #86efac !important;
    font-family: 'JetBrains Mono', monospace;
}

.warn-box {
    background: linear-gradient(135deg, #1f1200 0%, #2a1800 100%);
    border-left: 3px solid #d97706;
    border-radius: 10px;
    padding: 18px 22px;
    margin: 10px 0;
    color: #fbbf24;
    font-size: 0.9rem;
}

.welcome-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px 40px;
    text-align: center;
}
.welcome-duck-wrap {
    position: relative;
    display: inline-block;
    margin-bottom: 8px;
}
.welcome-duck {
    font-size: 6rem;
    animation: float 3s ease-in-out infinite;
    display: inline-block;
    position: relative;
    z-index: 2;
}
.duck-glow {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 120px;
    height: 120px;
    background: radial-gradient(ellipse at center,
        rgba(250, 204, 21, 0.45) 0%,
        rgba(250, 204, 21, 0.18) 40%,
        rgba(250, 204, 21, 0.0) 72%);
    border-radius: 50%;
    animation: glow-pulse 3s ease-in-out infinite;
    z-index: 1;
    pointer-events: none;
}
@keyframes float {
    0%,100% { transform: translateY(0px); }
    50%      { transform: translateY(-14px); }
}
@keyframes glow-pulse {
    0%,100% { opacity: 0.7; transform: translate(-50%, -50%) scale(1); }
    50%      { opacity: 1;   transform: translate(-50%, -58%) scale(1.15); }
}
.welcome-title {
    font-size: 2.6rem;
    font-weight: 700;
    color: #e8f0ff;
    letter-spacing: -0.03em;
    margin-bottom: 6px;
}
.welcome-sub {
    color: #3a5a7a;
    font-size: 1rem;
    margin-bottom: 52px;
    font-weight: 300;
}
.steps-wrap {
    display: flex;
    gap: 20px;
    justify-content: center;
    flex-wrap: wrap;
    width: 100%;
    max-width: 820px;
}
.step-card {
    background: #0d1828;
    border: 1px solid #1e3050;
    border-radius: 14px;
    padding: 28px 22px;
    flex: 1;
    min-width: 175px;
    max-width: 215px;
    transition: border-color 0.25s, transform 0.25s;
}
.step-card:hover { border-color: #2563eb; transform: translateY(-5px); }
.step-icon  { font-size: 2rem; margin-bottom: 12px; }
.step-num   { font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #2563eb; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 6px; }
.step-title { font-size: 1rem; font-weight: 600; color: #dce4f0; margin-bottom: 6px; }
.step-desc  { font-size: 0.78rem; color: #3a5a7a; line-height: 1.5; }

.badge-raw     { background: #1e3050; color: #60a5fa; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; }
.badge-cleaned { background: #14532d; color: #4ade80; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; }

.chart-rec-badge {
    background: #0d1828;
    border: 1px solid #1e3050;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 0.78rem;
    color: #60a5fa;
    margin-bottom: 14px;
    display: inline-block;
}

.chart-center-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
}

.sidebar-footer {
    border-top: 1px solid #1e2a40;
    padding: 12px 16px;
    font-size: 0.7rem;
    color: #2a4060 !important;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1.7;
    margin-top: 24px;
}
.sidebar-footer .dot { color: #16a34a !important; }

hr { border-color: #1e2a40 !important; }
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── DB ────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_con():
    return duckdb.connect(DB_PATH)

con = get_con()

# ── Cached data access ────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def get_table_metadata(_con, table: str) -> dict:
    """Retrieve schema and row count WITHOUT loading data into RAM."""
    # Get column type info from DuckDB
    info = _con.execute(f"DESCRIBE \"{table}\"").fetchall()
    
    num_cols, cat_cols, date_cols = [], [], []
    
    for col_name, col_type, null_val, key, def_val, extra in info:
        ct = col_type.upper()
        if any(t in ct for t in ['INT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC']):
            num_cols.append(col_name)
        elif any(t in ct for t in ['DATE', 'TIME', 'TIMESTAMP']):
            date_cols.append(col_name)
        else:
            cat_cols.append(col_name)
            
    # Count rows using SQL
    row_count = _con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    
    return {
        "columns": [r[0] for r in info],
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "date_cols": date_cols,
        "row_count": row_count
    }

@st.cache_data(ttl=300, show_spinner=False)
def load_preview(_con, table: str, n: int = 100) -> pd.DataFrame:
    """Fetch only the first N rows — fast even for huge tables."""
    return _con.execute(f'SELECT * FROM "{table}" LIMIT {n}').df()

@st.cache_data(ttl=300, show_spinner=False)
def load_row_count(table: str) -> int:
    """Count rows without pulling the whole table."""
    _con = get_con()
    return _con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]

# ── Ingestion ─────────────────────────────────────────────────────────────────

SMALL_THRESHOLD = 50 * 1024 * 1024   # 50 MB

def _table_name(stem: str) -> str:
    return stem.replace(" ","_").replace("-","_").replace(".","_").lower()

def _pandas_ingest(con, data: bytes, ext: str, table: str) -> str:
    """Fast path: load into pandas from memory, then push to DuckDB."""
    from io import BytesIO
    buf = BytesIO(data)
    if ext == ".csv":
        try:    df = pd.read_csv(buf, encoding="utf-8", low_memory=False)
        except:
            buf.seek(0)
            df = pd.read_csv(buf, encoding="latin-1", low_memory=False)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(buf)
    elif ext == ".parquet":
        df = pd.read_parquet(buf)
    elif ext == ".json":
        try:
            df = pd.read_json(buf)
        except:
            buf.seek(0)
            raw = json.load(buf)
            if isinstance(raw, list):
                df = pd.json_normalize(raw)
            elif isinstance(raw, dict):
                for key in raw:
                    if isinstance(raw[key], list):
                        df = pd.json_normalize(raw[key])
                        break
                else:
                    df = pd.json_normalize([raw])
    else:
        return None

    con.register("_tmp_ingest", df)
    con.execute(f'CREATE OR REPLACE TABLE "{table}" AS SELECT * FROM _tmp_ingest')
    con.unregister("_tmp_ingest")
    return table

def _duckdb_ingest(con, data: bytes, ext: str, table: str) -> str:
    """Large-file path: write to tempfile, let DuckDB stream directly from disk."""
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    p = tmp_path.replace("'", "''")
    try:
        if ext == ".csv":
            con.execute(f"""
                CREATE OR REPLACE TABLE "{table}" AS
                SELECT * FROM read_csv_auto('{p}',
                    header        = true,
                    ignore_errors = true,
                    sample_size   = -1,
                    all_varchar   = false,
                    auto_detect   = true)
            """)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(tmp_path)
            con.register("_tmp_ingest", df)
            con.execute(f'CREATE OR REPLACE TABLE "{table}" AS SELECT * FROM _tmp_ingest')
            con.unregister("_tmp_ingest")
        elif ext == ".parquet":
            con.execute(f"""
                CREATE OR REPLACE TABLE "{table}" AS
                SELECT * FROM read_parquet('{p}')
            """)
        elif ext == ".json":
            con.execute(f"""
                CREATE OR REPLACE TABLE "{table}" AS
                SELECT * FROM read_json_auto('{p}',
                    auto_detect   = true,
                    sample_size   = -1,
                    ignore_errors = true)
            """)
        else:
            return None
    finally:
        try: os.unlink(tmp_path)
        except: pass
    return table

def ingest_uploaded(con, uf) -> str:
    name  = Path(uf.name)
    table = _table_name(name.stem)
    ext   = name.suffix.lower()
    data  = uf.read()
    size  = len(data)

    try:
        if ext in (".xlsx", ".xls") or size < SMALL_THRESHOLD:
            return _pandas_ingest(con, data, ext, table)
        else:
            return _duckdb_ingest(con, data, ext, table)
    except Exception as e:
        raise RuntimeError(f"Ingest failed for {uf.name}: {e}") from e

def ingest_file(con, path: Path) -> str:
    """Ingest a file already on disk — always DuckDB native (no tempfile needed)."""
    table = _table_name(path.stem)
    ext   = path.suffix.lower()
    p     = str(path).replace("'", "''")
    try:
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(path)
            con.register("_tmp_ingest", df)
            con.execute(f'CREATE OR REPLACE TABLE "{table}" AS SELECT * FROM _tmp_ingest')
            con.unregister("_tmp_ingest")
        elif ext == ".csv":
            con.execute(f"""
                CREATE OR REPLACE TABLE "{table}" AS
                SELECT * FROM read_csv_auto('{p}',
                    header=true, ignore_errors=true,
                    sample_size=-1, auto_detect=true)
            """)
        elif ext == ".parquet":
            con.execute(f'CREATE OR REPLACE TABLE "{table}" AS SELECT * FROM read_parquet(\'{p}\')')
        elif ext == ".json":
            con.execute(f"""
                CREATE OR REPLACE TABLE "{table}" AS
                SELECT * FROM read_json_auto('{p}',
                    auto_detect=true, sample_size=-1, ignore_errors=true)
            """)
        else:
            return None
        return table
    except:
        return None

# ── Post-load pandas helpers ─────────────
def aggressive_numeric_inference(df: pd.DataFrame, threshold: float = 0.80) -> pd.DataFrame:
    for col in df.select_dtypes("object").columns:
        cleaned = df[col].astype(str).str.replace(",", "").str.strip()
        if pd.to_numeric(cleaned, errors="coerce").notna().sum() / max(len(df),1) >= threshold:
            df[col] = pd.to_numeric(cleaned, errors="coerce")
    return df

def list_tables(con):
    skip = {"_tmp","_tmp_ingest","_tmp_cleaned"}
    return [r[0] for r in con.execute("SHOW TABLES").fetchall() if r[0] not in skip]

def deep_clean_native(con, table: str) -> tuple[str, dict]:
    cleaned_name = f"{table}_cleaned"
    
    rows_before = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    
    columns = [r[0] for r in con.execute(f"DESCRIBE \"{table}\"").fetchall()]
    cols_before = len(columns)
    
    report = {
        "rows_before": rows_before, "cols_before": cols_before,
        "empty_cols_removed": [], "force_cast_cols":[],
        "inferred_cols":[], "duplicates_removed": 0,
    }

    valid_columns =[]
    for col in columns:
        non_null_count = con.execute(f'SELECT count("{col}") FROM "{table}"').fetchone()[0]
        
        if non_null_count == 0:
            report["empty_cols_removed"].append(col)
        else:
            valid_columns.append(col)

    select_exprs =[]
    
    for col in valid_columns:
        col_type = con.execute(f"SELECT typeof(\"{col}\") FROM \"{table}\" LIMIT 1").fetchone()[0]
        
        if col_type == 'VARCHAR':
            cast_query = f"""
            SELECT 
                COUNT("{col}") as total_non_null,
                COUNT(TRY_CAST(REPLACE(REPLACE("{col}", ',', ''), ' ', '') AS DOUBLE)) as castable
            FROM "{table}"
            """
            total_not_null, castable = con.execute(cast_query).fetchone()
            
            if total_not_null > 0 and (castable / total_not_null) >= 0.5:
                select_exprs.append(f"TRY_CAST(REPLACE(REPLACE(\"{col}\", ',', ''), ' ', '') AS DOUBLE) AS \"{col}\"")
                report["force_cast_cols"].append(col)
            else:
                select_exprs.append(f'"{col}"')
        else:
            select_exprs.append(f'"{col}"')
            
    select_clause = ",\n        ".join(select_exprs)
    
    clean_query = f"""
    CREATE OR REPLACE TABLE "{cleaned_name}" AS 
    SELECT DISTINCT 
        {select_clause}
    FROM "{table}"
    """
    con.execute(clean_query) 
    
    rows_after = con.execute(f'SELECT COUNT(*) FROM "{cleaned_name}"').fetchone()[0]
    
    report["rows_after"] = rows_after
    report["cols_after"] = len(valid_columns)
    report["duplicates_removed"] = rows_before - rows_after

    return cleaned_name, report

def wide_to_long(con, table: str) -> tuple[str, bool]:
    """
    Detect wide-format tables (date headers as columns) and melt to long format.
    Returns: (result_table_name, was_melted)
    """
    import re
    df = con.execute(f'SELECT * FROM "{table}"').df()

    date_pattern = re.compile(
        r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
        r'|(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})'
        r'|(\d{1,2}\s+\w+\s+\d{4})'
    )

    date_cols = [c for c in df.columns if date_pattern.search(str(c).replace(" ", ""))]

    if len(date_cols) < 3:
        return table, False

    id_vars  = [c for c in df.columns if c not in date_cols]

    df_long  = df.melt(id_vars=id_vars, value_vars=date_cols,
                       var_name="date", value_name="value")

    df_long["date"] = pd.to_datetime(
        df_long["date"].str.replace(r'\s+', '', regex=True),
        dayfirst=True, errors="coerce"
    )

    df_long["value"] = pd.to_numeric(
        df_long["value"].astype(str).str.replace(",", "").str.strip(),
        errors="coerce"
    )

    df_long = df_long.sort_values(["date"] + id_vars).reset_index(drop=True)

    long_name = f"{table}_long"
    con.register("_tmp_long", df_long)
    con.execute(f'CREATE OR REPLACE TABLE "{long_name}" AS SELECT * FROM _tmp_long')
    con.unregister("_tmp_long")

    return long_name, True

def smart_summary_native(con, table_name: str, meta: dict) -> str:
    """Analyze dataset statistics entirely within the database engine."""
    rows = meta["row_count"]
    cols = len(meta["columns"])
    
    label = "✨ Cleaned dataset" if table_name.endswith("_cleaned") else "Dataset"
    lines = [f"{label} <b>{table_name}</b> has <b>{rows:,} rows</b> and <b>{cols} columns</b>."]

    parts = []
    if meta["num_cols"]:  parts.append(f"{len(meta['num_cols'])} numeric")
    if meta["cat_cols"]:  parts.append(f"{len(meta['cat_cols'])} categorical")
    if meta["date_cols"]: parts.append(f"{len(meta['date_cols'])} datetime")
    if parts: lines.append(f"Column types: {', '.join(parts)}.")

    if rows > 0:
        null_selects = [f'SUM(CASE WHEN "{c}" IS NULL THEN 1 ELSE 0 END) AS "{c}"' for c in meta["columns"]]
        null_query = f'SELECT {",".join(null_selects)} FROM "{table_name}"'
        null_counts = con.execute(null_query).fetchone()
        
        dirty = []
        for col_name, null_count in zip(meta["columns"], null_counts):
            if null_count > 0:
                dirty.append((col_name, round(null_count / rows * 100, 1)))
        
        dirty = sorted(dirty, key=lambda x: x[1], reverse=True)
        
        if not dirty:
            lines.append("✅ <b>No missing values</b> — this dataset is clean.")
        else:
            alerts = [f"<b>{c}</b> ({v}%)" for c, v in dirty[:3]]
            lines.append(f"⚠️ <b>Dirty data detected</b> in: {', '.join(alerts)}.")

    return " ".join(lines)

# ── Export helpers ────────────────────────────────────────────────────────────
def export_table(con, table: str, fmt: str) -> bytes:
    """Export data directly from the DuckDB engine to disk (except Excel)."""
    import tempfile
    import os
    
    if fmt == "Excel":
        buf = BytesIO()
        df_temp = con.execute(f'SELECT * FROM "{table}"').df()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df_temp.to_excel(w, index=False)
        return buf.getvalue()

    ext_map = {"CSV": ".csv", "Parquet": ".parquet", "JSON": ".json"}
    ext = ext_map[fmt]
    
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = tmp.name
        
    try:
        p = tmp_path.replace("'", "''")
        if fmt == "CSV":
            con.execute(f"COPY \"{table}\" TO '{p}' (HEADER, FORMAT CSV)")
        elif fmt == "Parquet":
            con.execute(f"COPY \"{table}\" TO '{p}' (FORMAT PARQUET)")
        elif fmt == "JSON":
            con.execute(f"COPY \"{table}\" TO '{p}' (FORMAT JSON, ARRAY TRUE)")
            
        with open(tmp_path, "rb") as f:
            data = f.read()
        return data
    finally:
        try: os.unlink(tmp_path)
        except: pass

# ── Chart helpers (Native SQL Pushdown) ─────────────────────────────────────────
def get_recommended_charts_native(meta):
    """Providing chart recommendations based on metadata, without pulling data."""
    recs =[]
    num_cols  = meta["num_cols"]
    cat_cols  = meta["cat_cols"]
    date_cols = meta["date_cols"]
    
    if date_cols and num_cols:
        recs.append({"type":"line","x":date_cols[0],"y":num_cols[0],
                     "color": cat_cols[0] if cat_cols else None,
                     "label":f"📈 Trend of {num_cols[0]} over time"})
    if num_cols:
        recs.append({"type":"histogram","col":num_cols[0],
                     "label":f"📊 Distribution of {num_cols[0]}"})
    if cat_cols and num_cols and not date_cols:
        recs.append({"type":"bar","x":cat_cols[0],"y":num_cols[0],
                     "label":f"🏷️ Avg {num_cols[0]} by {cat_cols[0]}"})
    if len(num_cols) >= 2:
        recs.append({"type":"scatter","x":num_cols[0],"y":num_cols[1],
                     "label":f"🔵 {num_cols[0]} vs {num_cols[1]}"})
    return recs[:2]

PLOT_LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d1828", font_family="Sora")

WELCOME_HTML = """
<div class="welcome-wrap">
    <div class="welcome-duck-wrap">
        <div class="duck-glow"></div>
        <div class="welcome-duck">🦆</div>
    </div>
    <div class="welcome-title">Welcome to MALLARD</div>
    <div class="welcome-sub">Zero-config · 100% Local · No Cloud · No Setup</div>
    <div class="steps-wrap">
        <div class="step-card">
            <div class="step-icon">📂</div>
            <div class="step-num">Step 01</div>
            <div class="step-title">Upload Data</div>
            <div class="step-desc">Drag & drop CSV, Excel, Parquet, or JSON files into the sidebar.</div>
        </div>
        <div class="step-card">
            <div class="step-icon">🧹</div>
            <div class="step-num">Step 02</div>
            <div class="step-title">Clean & Repair</div>
            <div class="step-desc">Enable Deep Clean to fix data types, remove duplicates, and heal dirty columns.</div>
        </div>
        <div class="step-card">
            <div class="step-icon">📊</div>
            <div class="step-num">Step 03</div>
            <div class="step-title">Analyze</div>
            <div class="step-desc">Explore auto charts, write custom SQL, and read instant Smart Summaries.</div>
        </div>
        <div class="step-card">
            <div class="step-icon">💾</div>
            <div class="step-num">Step 04</div>
            <div class="step-title">Export</div>
            <div class="step-desc">Download cleaned data to CSV, Excel, Parquet, or JSON — ready to use anywhere.</div>
        </div>
    </div>
</div>
"""

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🦆 MALLARD")
    st.caption("Local Data Warehouse · Data Healer Edition")
    st.divider()

    st.markdown("### 📂 Upload Data")
    uploaded = st.file_uploader("Drag & drop your file here",
                                type=["csv","xlsx","xls","parquet","json"])
    if uploaded:
        with st.spinner(f"Loading {uploaded.name}..."):
            try:
                t = ingest_uploaded(con, uploaded)
                if t:
                    st.cache_data.clear()   
                    st.success(f"✅ {t} loaded!")
                else:
                    st.error("Unsupported file format.")
            except Exception as e:
                st.error(f"❌ Failed: {e}")

    if DATA_DIR.exists():
        files =[f for f in DATA_DIR.iterdir()
                 if f.suffix.lower() in {".csv",".xlsx",".xls",".parquet",".json"}]
        if files:
            with st.spinner("Scanning data/ folder..."):
                for f in files: ingest_file(con, f)

    st.divider()

    tables   = list_tables(con)
    n_tables = len(tables)

    if not tables:
        st.info("No data yet. Upload a file to get started.")
        st.markdown(f"""<div class="sidebar-footer">
        DATABASE &nbsp;mallard.duckdb<br>
        CONNECTION &nbsp;<span class="dot">● ACTIVE</span><br>
        TABLES &nbsp;0
        </div>""", unsafe_allow_html=True)

    else:
        st.markdown("### 🗂️ Select Table")
        selected = st.selectbox("", tables, label_visibility="collapsed")

        if selected.endswith("_cleaned"):
            st.markdown('<span class="badge-cleaned">✨ CLEANED</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-raw">📄 RAW</span>', unsafe_allow_html=True)

        st.divider()

        meta = get_table_metadata(con, selected)
        num_cols  = meta["num_cols"]
        cat_cols  = meta["cat_cols"]
        date_cols = meta["date_cols"]

        # ── Export ───────────────────────────────
        st.markdown("### 💾 Export Data")
        export_fmt = st.radio("Format:", ["CSV","Excel","Parquet","JSON"], horizontal=True)
        
        file_ext = {"CSV":"csv", "Excel":"xlsx", "Parquet":"parquet", "JSON":"json"}[export_fmt]
        mime_types = {
            "CSV": "text/csv",
            "Excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "Parquet": "application/octet-stream",
            "JSON": "application/json"
        }
        
        if st.download_button(
            label=f"⬇ Download {export_fmt}",
            data=export_table(con, selected, export_fmt),
            file_name=f"{selected}.{file_ext}",
            mime=mime_types[export_fmt]
        ):
            pass

        st.markdown("### 🧹 Data Healer")
        do_clean = st.toggle("Deep Clean & Repair Data", value=False)
        if do_clean:
            cleaned_name = f"{selected}_cleaned"
            if cleaned_name in list_tables(con):
                st.info(f"`{cleaned_name}` already exists. Select it from the dropdown.")
            else:
                if st.button("▶ Run Cleaning"):
                    with st.spinner("Cleaning data..."):
                        result_table, report = deep_clean_native(con, selected)
                    st.cache_data.clear()   
                    st.session_state["last_clean_report"] = report
                    st.session_state["last_clean_table"]  = result_table
                    st.success(f"✅ `{result_table}` created.")
                    st.rerun()
        
        st.markdown("#### 🔄 Wide → Long Converter")
        if st.button("▶ Convert Wide to Long"):
            long_name, success = wide_to_long(con, selected)
            if success:
                st.cache_data.clear()
                st.success(f"✅ `{long_name}` created — select it from the dropdown!")
                st.rerun()
            else:
                st.warning("No wide format detected.")

        st.divider()

        # ── Chart controls ─────────────────────────────────────────────────────
        st.markdown("### 📊 Chart Explorer")
        chart_type = st.selectbox("Chart Type",[
            "— Auto Recommend —",
            "Histogram","Bar (Average)","Scatter","Line"
        ], key="chart_type_select")

        chart_config = {}
        
        if chart_type == "Histogram":
            chart_config["col"] = st.selectbox("Column", num_cols, key="hist_col") if num_cols else None
        elif chart_type == "Bar (Average)":
            chart_config["x"]     = st.selectbox("Category (X)", cat_cols, key="bar_x") if cat_cols else None
            chart_config["y"]     = st.selectbox("Value (Y)", num_cols, key="bar_y") if num_cols else None
            chart_config["top_n"] = st.slider("Top N", 5, 30, 15, key="bar_topn")
        elif chart_type == "Scatter":
            chart_config["x"]     = st.selectbox("Column X", num_cols, key="scat_x") if num_cols else None
            chart_config["y"]     = st.selectbox("Column Y", num_cols, index=min(1,len(num_cols)-1), key="scat_y") if len(num_cols)>1 else None
            chart_config["color"] = st.selectbox("Color by", ["—"]+cat_cols, key="scat_color")
        elif chart_type == "Line":
            all_x = date_cols + num_cols + cat_cols
            chart_config["x"]     = st.selectbox("Column X", all_x, key="line_x") if all_x else None
            chart_config["y"]     = st.selectbox("Column Y", num_cols, key="line_y") if num_cols else None
            chart_config["color"] = st.selectbox("Color by", ["—"]+cat_cols, key="line_color")

        st.markdown("#### ⚙️ Chart Display")
        chart_height = st.slider("Chart Height (px)", 250, 900, 420, step=10, key="chart_height")
        chart_align  = st.radio("Position", ["Full Width", "Center"], horizontal=True, key="chart_align")

        if st.button("🔄 Reset Chart Settings"):
            for k in list(st.session_state.keys()):
                if k.startswith(("chart_","hist_","bar_","scat_","line_")):
                    del st.session_state[k]
            st.rerun()

        st.divider()

        # ── Delete table ───────────────────────────────────────────────────────
        st.markdown("### 🗑️ Delete Table")
        tabel_hapus = st.selectbox("Select table:", tables, key="del_select")
        if st.button("🗑 Delete This Table"):
            con.execute(f'DROP TABLE IF EXISTS "{tabel_hapus}"')
            st.cache_data.clear()
            if st.session_state.get("last_clean_table","").startswith(tabel_hapus.replace("_cleaned","")):
                st.session_state.pop("last_clean_report", None)
                st.session_state.pop("last_clean_table", None)
            st.success(f"✅ Table `{tabel_hapus}` deleted.")
            st.rerun()

        st.markdown(f"""<div class="sidebar-footer">
        DATABASE &nbsp;mallard.duckdb<br>
        CONNECTION &nbsp;<span class="dot">● ACTIVE</span><br>
        TABLES &nbsp;{n_tables}
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN AREA
# ══════════════════════════════════════════════════════════════════════════════
if not tables:
    st.markdown(WELCOME_HTML, unsafe_allow_html=True)
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
badge = '<span class="badge-cleaned">✨ CLEANED</span>' if selected.endswith("_cleaned") \
        else '<span class="badge-raw">📄 RAW</span>'
st.markdown(f"# {selected.replace('_',' ').title()} &nbsp;{badge}", unsafe_allow_html=True)

# ── Cleaning report ───────────────────────────────────────────────────────────
if ("last_clean_report" in st.session_state and
        st.session_state.get("last_clean_table","").replace("_cleaned","") == selected.replace("_cleaned","")):
    r = st.session_state["last_clean_report"]

    col_rows_parts = []
    for c in r["force_cast_cols"]:
        col_rows_parts.append(f"<tr><td>{c}</td><td>Force-cast → NUMERIC</td><td>✅ Healthy</td></tr>")
    for c in r["inferred_cols"]:
        col_rows_parts.append(f"<tr><td>{c}</td><td>Inferred → NUMERIC</td><td>✅ Healthy</td></tr>")
    for c in r["empty_cols_removed"]:
        col_rows_parts.append(f"<tr><td>{c}</td><td>100% empty → removed</td><td>🗑️ Removed</td></tr>")

    col_table_html = "<table><tr><th>Column</th><th>Action</th><th>Status</th></tr>" + "".join(col_rows_parts) + "</table>" if col_rows_parts else ""

    clean_report_html = (
        '<div class="clean-box">'
        "✅ <b>Deep Clean complete.</b><br>"
        f"🗑️ Duplicates removed: <b>{r['duplicates_removed']:,} rows</b> &nbsp;|&nbsp;"
        f"📭 Empty columns removed: <b>{len(r['empty_cols_removed'])}</b><br>"
        f"📊 <b>{r['rows_before']:,}</b> → <b>{r['rows_after']:,} rows</b> &nbsp;|&nbsp;"
        f"<b>{r['cols_before']}</b> → <b>{r['cols_after']} columns</b>"
        + col_table_html
        + "</div>"
    )
    st.markdown(clean_report_html, unsafe_allow_html=True)

# ── Metrics ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rows",        f"{meta['row_count']:,}")
c2.metric("Columns",     len(meta["columns"]))
c3.metric("Numeric",     len(num_cols))
c4.metric("Categorical", len(cat_cols))
c5.metric("Date/Time",   len(date_cols)) 

st.divider()

# ── Smart Summary ──────────────────────────────────────────────────────────────
st.markdown("### 🧠 Smart Summary")
st.markdown(f'<div class="summary-box">{smart_summary_native(con, selected, meta)}</div>', unsafe_allow_html=True)

if len(num_cols) == 0 and not selected.endswith("_cleaned"):
    st.markdown(
        '<div class="warn-box">⚠️ <b>No numeric columns detected.</b> Enable Deep Clean in the sidebar.</div>',
        unsafe_allow_html=True
    )

st.divider()

st.markdown("### 🔍 Data Preview")
st.dataframe(load_preview(con, selected, n=100), use_container_width=True)

st.divider()

# ── Visualization ──────────────────────────────────────────────────────────────
st.markdown("### 📊 Visualization")

_height = st.session_state.get("chart_height", 420)
_align  = st.session_state.get("chart_align", "Full Width")

def _render_chart(fig):
    if fig is None: return
    fig.update_layout(**PLOT_LAYOUT, height=_height)
    if _align == "Center":
        col_l, col_m, col_r = st.columns([1, 3, 1])
        col_m.plotly_chart(fig, use_container_width=True)
    else:
        st.plotly_chart(fig, use_container_width=True)

fig = None

if chart_type == "— Auto Recommend —":
    recs = get_recommended_charts_native(meta)
    if recs:
        st.markdown('<div class="chart-rec-badge">✨ Auto Recommended — based on your data structure</div>', unsafe_allow_html=True)
        rec = recs[0]
        st.info(f"Recommendation: {rec['label']}. Please select a chart type manually in the sidebar for full customization.")
    else:
        st.info("Not enough columns for auto-recommend. Please select a chart type manually.")

elif chart_type == "Histogram" and chart_config.get("col"):
    query = f'SELECT "{chart_config["col"]}" FROM "{selected}" USING SAMPLE 50000'
    df_chart = con.execute(query).df()
    fig = px.histogram(df_chart, x=chart_config["col"], nbins=40,
                       title=f"Distribution — {chart_config['col']} (Sampled)",
                       template="plotly_dark", color_discrete_sequence=["#3b82f6"])

elif chart_type == "Bar (Average)" and chart_config.get("x") and chart_config.get("y"):
    query = f"""
        SELECT "{chart_config['x']}", AVG("{chart_config['y']}") as "{chart_config['y']}"
        FROM "{selected}"
        GROUP BY "{chart_config['x']}"
        ORDER BY "{chart_config['y']}" DESC
        LIMIT {chart_config.get('top_n', 15)}
    """
    df_chart = con.execute(query).df()
    fig = px.bar(df_chart, x=chart_config["x"], y=chart_config["y"],
                 title=f"Avg {chart_config['y']} by {chart_config['x']}",
                 template="plotly_dark", color_discrete_sequence=["#3b82f6"])

elif chart_type == "Scatter" and chart_config.get("x") and chart_config.get("y"):
    col_color = f', "{chart_config["color"]}"' if chart_config.get("color") and chart_config["color"] != "—" else ""
    query = f'SELECT "{chart_config["x"]}", "{chart_config["y"]}" {col_color} FROM "{selected}" USING SAMPLE 10000'
    df_chart = con.execute(query).df()
    fig = px.scatter(df_chart, x=chart_config["x"], y=chart_config["y"],
                     color=None if not chart_config.get("color") or chart_config["color"]=="—" else chart_config["color"],
                     title=f"{chart_config['x']} vs {chart_config['y']} (Max 10k pts)",
                     template="plotly_dark", opacity=0.7)

elif chart_type == "Line" and chart_config.get("x") and chart_config.get("y"):
    col_color = f', "{chart_config["color"]}"' if chart_config.get("color") and chart_config["color"] != "—" else ""
    query = f'SELECT "{chart_config["x"]}", "{chart_config["y"]}" {col_color} FROM "{selected}" ORDER BY "{chart_config["x"]}" LIMIT 10000'
    df_chart = con.execute(query).df()
    fig = px.line(df_chart, x=chart_config["x"], y=chart_config["y"],
                  color=None if not chart_config.get("color") or chart_config["color"]=="—" else chart_config["color"],
                  title=f"{chart_config['y']} over {chart_config['x']}",
                  template="plotly_dark")

_render_chart(fig)

st.divider()

# ── Descriptive Stats (DuckDB Native Summarize) ────────────────────────────────
with st.expander("📈 Descriptive Statistics"):
    try:
        stats_df = con.execute(f'SUMMARIZE "{selected}"').df()
        st.dataframe(stats_df, use_container_width=True)
    except:
        st.info("Descriptive statistics are not available for this dataset.")

# ── Custom SQL + Export ────────────────────────────────────────────────────────
with st.expander("🛠️ Power User — Custom SQL"):
    sql = st.text_area("Query:", value=f'SELECT * FROM "{selected}" LIMIT 50', height=120)
    if st.button("▶ Run Query"):
        try:
            result = con.execute(sql).df()
            st.dataframe(result, use_container_width=True)
            st.caption(f"{len(result):,} rows returned")

            st.markdown("**⬇ Export Query Result:**")
            exp_cols = st.columns(4)
            exp_cols[0].download_button(
                "CSV", data=result.to_csv(index=False).encode('utf-8'),
                file_name="query_result.csv", mime="text/csv"
            )
            
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                result.to_excel(w, index=False)
            exp_cols[1].download_button(
                "Excel", data=buf.getvalue(),
                file_name="query_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            buf_pq = BytesIO()
            result.to_parquet(buf_pq, index=False)
            exp_cols[2].download_button(
                "Parquet", data=buf_pq.getvalue(),
                file_name="query_result.parquet",
                mime="application/octet-stream"
            )
            
            exp_cols[3].download_button(
                "JSON", data=result.to_json(orient="records", indent=2).encode('utf-8'),
                file_name="query_result.json",
                mime="application/json"
            )
        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.caption("🦆 MALLARD · Data Healer Edition · DuckDB + Streamlit · 100% Local & Free")