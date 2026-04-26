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
def load_table(table: str) -> pd.DataFrame:
    """
    Load a full table from DuckDB into pandas — cached for 5 minutes.
    Cache is busted automatically when table name changes (e.g. after cleaning).
    Call st.cache_data.clear() after any write operation that mutates a table.
    """
    _con = get_con()
    df   = _con.execute(f'SELECT * FROM "{table}"').df()
    for col in df.columns:
        if any(k in col.lower() for k in ["tanggal","date","tgl","time","waktu"]):
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

@st.cache_data(ttl=300, show_spinner=False)
def load_preview(table: str, n: int = 100) -> pd.DataFrame:
    """Fetch only the first N rows — fast even for huge tables."""
    _con = get_con()
    df   = _con.execute(f'SELECT * FROM "{table}" LIMIT {n}').df()
    for col in df.columns:
        if any(k in col.lower() for k in ["tanggal","date","tgl","time","waktu"]):
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

@st.cache_data(ttl=300, show_spinner=False)
def load_row_count(table: str) -> int:
    """Count rows without pulling the whole table."""
    _con = get_con()
    return _con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]

# ── Ingestion ─────────────────────────────────────────────────────────────────
# Hybrid strategy:
#   < SMALL_THRESHOLD  → pandas (pure RAM, zero disk overhead, fastest for small files)
#   >= SMALL_THRESHOLD → DuckDB native via tempfile (streaming, handles multi-GB)
# Excel always uses pandas — DuckDB has no built-in xlsx reader.

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
            # No native DuckDB xlsx reader — always pandas regardless of size
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
            # small file or Excel → pandas path (fast, pure RAM)
            return _pandas_ingest(con, data, ext, table)
        else:
            # large file → DuckDB native streaming
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

# ── Post-load pandas helpers (only used AFTER data is in DuckDB) ─────────────
def aggressive_numeric_inference(df: pd.DataFrame, threshold: float = 0.80) -> pd.DataFrame:
    for col in df.select_dtypes("object").columns:
        cleaned = df[col].astype(str).str.replace(",", "").str.strip()
        if pd.to_numeric(cleaned, errors="coerce").notna().sum() / max(len(df),1) >= threshold:
            df[col] = pd.to_numeric(cleaned, errors="coerce")
    return df

def list_tables(con):
    skip = {"_tmp","_tmp_ingest","_tmp_cleaned"}
    return [r[0] for r in con.execute("SHOW TABLES").fetchall() if r[0] not in skip]

def deep_clean(con, table: str) -> tuple[str, dict]:
    cleaned_name = f"{table}_cleaned"
    df = con.execute(f'SELECT * FROM "{table}"').df()
    report = {
        "rows_before": len(df), "cols_before": len(df.columns),
        "empty_cols_removed": [], "force_cast_cols": [],
        "inferred_cols": [], "duplicates_removed": 0,
    }
    empty = [c for c in df.columns if df[c].isna().all()]
    df    = df.drop(columns=empty)
    report["empty_cols_removed"] = empty

    key_patterns = ["harga","jumlah","total","qty","amount","price",
                    "value","rating","count","revenue","cost","salary"]
    for col in df.select_dtypes("object").columns:
        if any(p in col.lower() for p in key_patterns):
            s = pd.to_numeric(df[col].astype(str).str.replace(",","").str.strip(), errors="coerce")
            if s.notna().sum() / max(len(df),1) >= 0.5:
                df[col] = s
                report["force_cast_cols"].append(col)

    before_types = df.dtypes.copy()
    df = aggressive_numeric_inference(df, threshold=0.75)
    for col in df.columns:
        if str(before_types.get(col)) == "object" and col not in report["force_cast_cols"]:
            if df[col].dtype != before_types.get(col):
                report["inferred_cols"].append(col)

    before_dedup = len(df)
    df = df.drop_duplicates()
    report["duplicates_removed"] = before_dedup - len(df)
    report["rows_after"]  = len(df)
    report["cols_after"]  = len(df.columns)

    con.register("_tmp_cleaned", df)
    con.execute(f'CREATE OR REPLACE TABLE "{cleaned_name}" AS SELECT * FROM _tmp_cleaned')
    con.unregister("_tmp_cleaned")

    _, was_wide = wide_to_long(con, table)
    if was_wide:
        report["wide_to_long"] = True

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

def smart_summary(df: pd.DataFrame, table_name: str) -> str:
    rows, cols  = df.shape
    num_cols    = df.select_dtypes("number").columns.tolist()
    cat_cols    = df.select_dtypes("object").columns.tolist()
    date_cols   = df.select_dtypes("datetime").columns.tolist()
    dirty       = (df.isnull().sum() / rows * 100).round(1)
    dirty       = dirty[dirty > 0].sort_values(ascending=False)
    label       = "✨ Cleaned dataset" if table_name.endswith("_cleaned") else "Dataset"
    lines       = [f"{label} <b>{table_name}</b> has <b>{rows:,} rows</b> and <b>{cols} columns</b>."]

    parts = []
    if num_cols:  parts.append(f"{len(num_cols)} numeric")
    if cat_cols:  parts.append(f"{len(cat_cols)} categorical")
    if date_cols: parts.append(f"{len(date_cols)} datetime")
    if parts: lines.append(f"Column types: {', '.join(parts)}.")

    if dirty.empty:
        lines.append("✅ <b>No missing values</b> — this dataset is clean.")
    else:
        alerts = [f"<b>{c}</b> ({v}%)" for c,v in dirty.head(3).items()]
        lines.append(f"⚠️ <b>Dirty data detected</b> in: {', '.join(alerts)}.")

    if num_cols:
        d = df[num_cols[0]].dropna()
        if not d.empty:
            lines.append(f"Column <b>{num_cols[0]}</b>: "
                         f"max <b>{d.max():,.2f}</b>, min <b>{d.min():,.2f}</b>, "
                         f"mean <b>{d.mean():,.2f}</b>.")

    if cat_cols:
        vc = df[cat_cols[0]].value_counts()
        if not vc.empty:
            lines.append(f"Most dominant in <b>{cat_cols[0]}</b>: <b>{vc.idxmax()}</b> "
                         f"({vc.max():,} entries, {round(vc.max()/rows*100,1)}%).")

    if date_cols:
        d = df[date_cols[0]].dropna()
        if not d.empty:
            lines.append(f"Date range: <b>{d.min().date()}</b> — <b>{d.max().date()}</b>.")

    return " ".join(lines)

# ── Export helpers ────────────────────────────────────────────────────────────
def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")

def df_to_excel_bytes(df):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    return buf.getvalue()

def df_to_parquet_bytes(df):
    buf = BytesIO()
    df.to_parquet(buf, index=False)
    return buf.getvalue()

def df_to_json_bytes(df):
    return df.to_json(orient="records", indent=2, force_ascii=False).encode("utf-8")

# ── Chart helpers ─────────────────────────────────────────────────────────────
def get_recommended_charts(df):
    recs      = []
    num_cols  = df.select_dtypes("number").columns.tolist()
    cat_cols  = df.select_dtypes("object").columns.tolist()
    date_cols = df.select_dtypes("datetime").columns.tolist()
    if date_cols and num_cols:
        recs.append({"type":"line","x":date_cols[0],"y":num_cols[0],
                     "color": cat_cols[1] if len(cat_cols)>1 else None,
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

def render_rec(rec, df):
    t = rec["type"]
    if t == "line":
        return px.line(df.sort_values(rec["x"]), x=rec["x"], y=rec["y"],
                       color=rec.get("color"), title=rec["label"], template="plotly_dark")
    elif t == "histogram":
        return px.histogram(df, x=rec["col"], nbins=40, title=rec["label"],
                            template="plotly_dark", color_discrete_sequence=["#3b82f6"])
    elif t == "bar":
        grp = df.groupby(rec["x"])[rec["y"]].mean().nlargest(15).reset_index()
        return px.bar(grp, x=rec["x"], y=rec["y"], title=rec["label"],
                      template="plotly_dark", color_discrete_sequence=["#3b82f6"])
    elif t == "scatter":
        return px.scatter(df, x=rec["x"], y=rec["y"], title=rec["label"],
                          template="plotly_dark", opacity=0.7)

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
                    st.cache_data.clear()   # bust so new table shows fresh
                    st.success(f"✅ {t} loaded!")
                else:
                    st.error("Unsupported file format.")
            except Exception as e:
                st.error(f"❌ Failed: {e}")

    if DATA_DIR.exists():
        files = [f for f in DATA_DIR.iterdir()
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

        df = load_table(selected)

        num_cols  = df.select_dtypes("number").columns.tolist()
        cat_cols  = df.select_dtypes("object").columns.tolist()
        date_cols = df.select_dtypes("datetime").columns.tolist()

        # ── Export (available for ALL tables, not just cleaned) ───────────────
        st.markdown("### 💾 Export Data")
        export_fmt = st.radio("Format:", ["CSV","Excel","Parquet","JSON"], horizontal=True)
        if export_fmt == "CSV":
            st.download_button("⬇ Download CSV", data=df_to_csv_bytes(df),
                               file_name=f"{selected}.csv", mime="text/csv")
        elif export_fmt == "Excel":
            st.download_button("⬇ Download Excel", data=df_to_excel_bytes(df),
                               file_name=f"{selected}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        elif export_fmt == "Parquet":
            st.download_button("⬇ Download Parquet", data=df_to_parquet_bytes(df),
                               file_name=f"{selected}.parquet",
                               mime="application/octet-stream")
        elif export_fmt == "JSON":
            st.download_button("⬇ Download JSON", data=df_to_json_bytes(df),
                               file_name=f"{selected}.json",
                               mime="application/json")

        st.divider()

        # ── Deep Clean ────────────────────────────────────────────────────────
        st.markdown("### 🧹 Data Healer")
        do_clean = st.toggle("Deep Clean & Repair Data", value=False)
        if do_clean:
            cleaned_name = f"{selected}_cleaned"
            if cleaned_name in list_tables(con):
                st.info(f"`{cleaned_name}` already exists. Select it from the dropdown.")
            else:
                if st.button("▶ Run Cleaning"):
                    with st.spinner("Cleaning data..."):
                        result_table, report = deep_clean(con, selected)
                    st.cache_data.clear()   # bust so cleaned table loads fresh
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
                st.warning("No wide format detected. Column headers must look like dates.")

        st.divider()

        # ── Chart controls ─────────────────────────────────────────────────────
        st.markdown("### 📊 Chart Explorer")

        chart_type = st.selectbox("Chart Type", [
            "— Auto Recommend —",
            "Histogram","Bar (Average)","Scatter","Line","Box","Correlation Heatmap"
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
            all_x = date_cols+num_cols+cat_cols
            chart_config["x"]     = st.selectbox("Column X", all_x, key="line_x") if all_x else None
            chart_config["y"]     = st.selectbox("Column Y", num_cols, key="line_y") if num_cols else None
            chart_config["color"] = st.selectbox("Color by", ["—"]+cat_cols, key="line_color")
        elif chart_type == "Box":
            chart_config["x"] = st.selectbox("Category (X)", ["—"]+cat_cols, key="box_x")
            chart_config["y"] = st.selectbox("Value (Y)", num_cols, key="box_y") if num_cols else None

        # ── Chart size & position ─────────────────────────────────────────────
        st.markdown("#### ⚙️ Chart Display")
        chart_height = st.slider("Chart Height (px)", 250, 900, 420, step=10, key="chart_height")
        chart_align  = st.radio("Position", ["Full Width", "Center"], horizontal=True, key="chart_align")

        # ── Reset chart ───────────────────────────────────────────────────────
        if st.button("🔄 Reset Chart Settings"):
            for k in ["chart_type_select","hist_col","bar_x","bar_y","bar_topn",
                      "scat_x","scat_y","scat_color","line_x","line_y","line_color",
                      "box_x","box_y","chart_height","chart_align"]:
                if k in st.session_state:
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
# FIX #5: build the HTML string carefully so NO stray closing tags leak out
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

    if col_rows_parts:
        col_table_html = (
            "<table>"
            "<tr><th>Column</th><th>Action</th><th>Status</th></tr>"
            + "".join(col_rows_parts)
            + "</table>"
        )
    else:
        col_table_html = ""

    clean_report_html = (
        '<div class="clean-box">'
        "✅ <b>Deep Clean complete.</b><br>"
        f"🗑️ Duplicates removed: <b>{r['duplicates_removed']:,} rows</b> &nbsp;|&nbsp;"
        f"📭 Empty columns removed: <b>{len(r['empty_cols_removed'])}</b><br>"
        f"📊 <b>{r['rows_before']:,}</b> → <b>{r['rows_after']:,} rows</b> &nbsp;|&nbsp;"
        f"<b>{r['cols_before']}</b> → <b>{r['cols_after']} columns</b>"
        + col_table_html
        + (f'<br>🔄 <b>Wide → Long</b> version also created — check <code>{selected}_long</code> in the dropdown.' if r.get("wide_to_long") else "")
        + "</div>"
    )
    st.markdown(clean_report_html, unsafe_allow_html=True)

# ── Metrics ───────────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Rows",        f"{len(df):,}")
c2.metric("Columns",     len(df.columns))
c3.metric("Numeric",     len(num_cols))
c4.metric("Categorical", len(cat_cols))
c5.metric("Size",        f"{df.memory_usage(deep=True).sum()/1e6:.2f} MB")

st.divider()

# ── Smart Summary ──────────────────────────────────────────────────────────────
st.markdown("### 🧠 Smart Summary")
st.markdown(f'<div class="summary-box">{smart_summary(df, selected)}</div>', unsafe_allow_html=True)

if len(num_cols) == 0 and not selected.endswith("_cleaned"):
    st.markdown(
        '<div class="warn-box">'
        "⚠️ <b>No numeric columns detected.</b> Your data may contain dirty values like 'N/A' or 'Unknown'. "
        "Enable <b>🧹 Deep Clean & Repair Data</b> in the sidebar to fix this automatically."
        "</div>",
        unsafe_allow_html=True
    )

st.divider()

st.markdown("### 🔍 Data Preview")
st.dataframe(load_preview(selected, n=100), use_container_width=True)

st.divider()

# ── Visualization ──────────────────────────────────────────────────────────────
st.markdown("### 📊 Visualization")

# Grab chart settings from session state (with defaults if reset)
_height = st.session_state.get("chart_height", 420)
_align  = st.session_state.get("chart_align", "Full Width")

def _render_chart(fig):
    """Render chart respecting height and alignment settings."""
    if fig is None:
        return
    fig.update_layout(**PLOT_LAYOUT, height=_height)
    if _align == "Center":
        col_l, col_m, col_r = st.columns([1, 3, 1])
        col_m.plotly_chart(fig, use_container_width=True)
    else:
        st.plotly_chart(fig, use_container_width=True)

if chart_type == "— Auto Recommend —":
    recs = get_recommended_charts(df)
    if recs:
        st.markdown('<div class="chart-rec-badge">✨ Auto Recommended — based on your data structure</div>',
                    unsafe_allow_html=True)
        if _align == "Center":
            # center each chart in its own centered column block
            for rec in recs:
                fig = render_rec(rec, df)
                if fig:
                    fig.update_layout(**PLOT_LAYOUT, height=_height)
                    col_l, col_m, col_r = st.columns([1, 3, 1])
                    col_m.plotly_chart(fig, use_container_width=True)
        else:
            cols_c = st.columns(len(recs))
            for i, rec in enumerate(recs):
                fig = render_rec(rec, df)
                if fig:
                    fig.update_layout(**PLOT_LAYOUT, height=_height)
                    cols_c[i].plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough columns for auto-recommend. Select a chart type manually.")
else:
    if not num_cols and chart_type not in ["Bar (Average)"]:
        st.info("No numeric columns detected. Run Deep Clean first.")
    else:
        fig = None
        if chart_type == "Histogram" and chart_config.get("col"):
            fig = px.histogram(df, x=chart_config["col"], nbins=40,
                               title=f"Distribution — {chart_config['col']}",
                               template="plotly_dark", color_discrete_sequence=["#3b82f6"])
        elif chart_type == "Bar (Average)" and chart_config.get("x") and chart_config.get("y"):
            grp = df.groupby(chart_config["x"])[chart_config["y"]].mean()\
                    .nlargest(chart_config["top_n"]).reset_index()
            fig = px.bar(grp, x=chart_config["x"], y=chart_config["y"],
                         title=f"Avg {chart_config['y']} by {chart_config['x']}",
                         template="plotly_dark", color_discrete_sequence=["#3b82f6"])
        elif chart_type == "Scatter" and chart_config.get("x") and chart_config.get("y"):
            fig = px.scatter(df, x=chart_config["x"], y=chart_config["y"],
                             color=None if chart_config["color"]=="—" else chart_config["color"],
                             title=f"{chart_config['x']} vs {chart_config['y']}",
                             template="plotly_dark", opacity=0.7)
        elif chart_type == "Line" and chart_config.get("x") and chart_config.get("y"):
            fig = px.line(df.sort_values(chart_config["x"]),
                          x=chart_config["x"], y=chart_config["y"],
                          color=None if chart_config["color"]=="—" else chart_config["color"],
                          title=f"{chart_config['y']} over {chart_config['x']}",
                          template="plotly_dark")
        elif chart_type == "Box" and chart_config.get("y"):
            fig = px.box(df,
                         x=None if chart_config["x"]=="—" else chart_config["x"],
                         y=chart_config["y"],
                         title=f"Box Plot — {chart_config['y']}",
                         template="plotly_dark", color_discrete_sequence=["#3b82f6"])
        elif chart_type == "Correlation Heatmap":
            if len(num_cols) >= 2:
                corr = df[num_cols].corr().round(2)
                fig  = px.imshow(corr, text_auto=True, title="Correlation Heatmap",
                                 template="plotly_dark", color_continuous_scale="Blues")
            else:
                st.info("Need at least 2 numeric columns for a heatmap.")
        _render_chart(fig)

st.divider()

# ── Descriptive Stats ──────────────────────────────────────────────────────────
with st.expander("📈 Descriptive Statistics"):
    st.dataframe(df.describe(include="all").T, use_container_width=True)

# ── Custom SQL + Export ────────────────────────────────────────────────────────
with st.expander("🛠️ Power User — Custom SQL"):
    sql = st.text_area("Query:", value=f'SELECT * FROM "{selected}" LIMIT 50', height=120)
    if st.button("▶ Run Query"):
        try:
            result = con.execute(sql).df()
            st.dataframe(result, use_container_width=True)
            st.caption(f"{len(result):,} rows returned")

            # Export results
            st.markdown("**⬇ Export Query Result:**")
            exp_cols = st.columns(4)
            exp_cols[0].download_button(
                "CSV", data=df_to_csv_bytes(result),
                file_name="query_result.csv", mime="text/csv"
            )
            exp_cols[1].download_button(
                "Excel", data=df_to_excel_bytes(result),
                file_name="query_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            exp_cols[2].download_button(
                "Parquet", data=df_to_parquet_bytes(result),
                file_name="query_result.parquet",
                mime="application/octet-stream"
            )
            exp_cols[3].download_button(
                "JSON", data=df_to_json_bytes(result),
                file_name="query_result.json",
                mime="application/json"
            )
        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.caption("🦆 MALLARD · Data Healer Edition · DuckDB + Streamlit · 100% Local & Free")