import io
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="MALLARD", page_icon="🦆", layout="wide")

DATA_DIR = Path("data")
DB_PATH  = "mallard.duckdb"

# Auto-create data/ folder and DB if it does not exist
DATA_DIR.mkdir(exist_ok=True)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Sora:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Sora', sans-serif !important; }

.stApp { background-color: #080c14 !important; color: #dce4f0; }

[data-testid="metric-container"] {
    background: linear-gradient(135deg, #0d1828 0%, #111e30 100%) !important;
    border: 1px solid #1e3050 !important;
    border-radius: 12px !important;
    padding: 18px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
}
[data-testid="metric-container"] label {
    color: #5a7a9a !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e8f0ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.6rem !important;
}

.stButton > button {
    background: linear-gradient(135deg, #1a4fd6, #2563eb) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; padding: 9px 22px !important;
    font-weight: 600 !important; font-family: 'Sora', sans-serif !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1e40af, #1d4ed8) !important;
    transform: translateY(-1px) !important;
}

.summary-box {
    background: linear-gradient(135deg, #0d1828 0%, #0f1f35 100%);
    border-left: 3px solid #2563eb; border-radius: 10px;
    padding: 22px 26px; margin: 12px 0; line-height: 1.9;
    color: #b8cce0; font-size: 0.95rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}
.clean-box {
    background: linear-gradient(135deg, #0a1f12 0%, #0d2a18 100%);
    border-left: 3px solid #16a34a; border-radius: 10px;
    padding: 18px 22px; margin: 10px 0; line-height: 1.9;
    color: #a0d4b0; font-size: 0.9rem;
}
.warn-box {
    background: linear-gradient(135deg, #1f1200 0%, #2a1800 100%);
    border-left: 3px solid #d97706; border-radius: 10px;
    padding: 18px 22px; margin: 10px 0;
    color: #fbbf24; font-size: 0.9rem;
}
.badge-raw {
    background: #1e3050; color: #60a5fa;
    padding: 2px 10px; border-radius: 20px;
    font-size: 0.75rem; font-family: 'JetBrains Mono', monospace;
}
.badge-cleaned {
    background: #14532d; color: #4ade80;
    padding: 2px 10px; border-radius: 20px;
    font-size: 0.75rem; font-family: 'JetBrains Mono', monospace;
}
.col-tag {
    display: inline-block; background: #0d2a18;
    border: 1px solid rgba(22,163,74,0.27); color: #4ade80;
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
    padding: 2px 9px; border-radius: 20px; margin: 2px 3px 2px 0;
}
.welcome-wrap {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 60px 20px 40px; text-align: center;
}
.welcome-duck {
    font-size: 6rem; line-height: 1; margin-bottom: 8px;
    filter: drop-shadow(0 0 32px rgba(37,99,235,0.5));
    animation: float 3s ease-in-out infinite;
}
@keyframes float {
    0%,100% { transform: translateY(0); }
    50%      { transform: translateY(-10px); }
}
.welcome-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.8rem; font-weight: 600;
    color: #e8f0ff; letter-spacing: 0.12em; margin-bottom: 6px;
}
.welcome-sub { font-size: 1rem; color: #5a7a9a; margin-bottom: 48px; }
.step-grid {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 20px; max-width: 780px; width: 100%; margin-bottom: 40px;
}
.step-card {
    background: linear-gradient(135deg, #0d1828, #111e30);
    border: 1px solid #1e3050; border-radius: 14px;
    padding: 28px 20px;
}
.step-num  { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #2563eb; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 10px; }
.step-icon { font-size: 2rem; margin-bottom: 10px; }
.step-title { font-size: 0.95rem; font-weight: 600; color: #dce4f0; margin-bottom: 6px; }
.step-desc  { font-size: 0.82rem; color: #5a7a9a; line-height: 1.6; }
.fmt-label  { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #2d4a6a; }

hr { border-color: #1e2a40 !important; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── DB ────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_con():
    c = duckdb.connect(DB_PATH)
    c.execute("SET memory_limit = '4GB'") 
    c.execute("SET threads = 8")
    return c

con = get_con()

# ── Helpers ───────────────────────────────────────────────────────────────────
def is_date_column_header(col):
    try:
        pd.to_datetime(col, dayfirst=True)
        return True
    except:
        return False

def aggressive_numeric_inference(df, threshold=0.80):
    for col in df.select_dtypes("object").columns:
        cleaned = df[col].astype(str).str.replace(",", "").str.strip()
        ratio = pd.to_numeric(cleaned, errors="coerce").notna().sum() / max(len(df), 1)
        if ratio >= threshold:
            df[col] = pd.to_numeric(cleaned, errors="coerce")
    return df

def smart_date_parse(series):
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d",
               "%d %b %Y", "%d %B %Y", "%B %Y", "%b %Y"]
    result    = pd.Series([pd.NaT] * len(series), index=series.index)
    remaining = series.copy()
    for fmt in formats:
        parsed = pd.to_datetime(remaining, format=fmt, errors="coerce", dayfirst=True)
        filled = parsed.notna()
        result[filled]    = parsed[filled]
        remaining[filled] = pd.NaT
    fallback = pd.to_datetime(remaining, errors="coerce", dayfirst=True)
    result[result.isna()] = fallback[result.isna()]
    return result

def looks_like_date_column(series, threshold=0.60):
    if series.dtype != object:
        return False
    sample = series.dropna().head(200).astype(str)
    return pd.to_datetime(sample, errors="coerce", dayfirst=True).notna().mean() >= threshold

def _process_df(df):
    date_header_cols = [c for c in df.columns if is_date_column_header(str(c))]
    if len(date_header_cols) > 3:
        id_cols = [c for c in df.columns if c not in date_header_cols]
        df = df.melt(id_vars=id_cols, value_vars=date_header_cols,
                     var_name="Date", value_name="Value")
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
        df["Value"]   = pd.to_numeric(
            df["Value"].astype(str).str.replace(",", "").str.strip(), errors="coerce")
        return df
    df = aggressive_numeric_inference(df)
    for col in df.select_dtypes("object").columns:
        if looks_like_date_column(df[col]):
            df[col] = smart_date_parse(df[col].astype(str))
    return df

def ingest_file(con, path):
    table = path.stem.replace(" ", "_").replace("-", "_").lower()
    ext = path.suffix.lower()
    try:
        if ext == ".csv":
            con.execute(f"CREATE OR REPLACE TABLE '{table}' AS SELECT * FROM read_csv_auto('{path}')")
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(path)
            con.register("_tmp_excel", df)
            con.execute(f"CREATE OR REPLACE TABLE '{table}' AS SELECT * FROM _tmp_excel")
            con.unregister("_tmp_excel")
        elif ext == ".parquet":
            con.execute(f"CREATE OR REPLACE TABLE '{table}' AS SELECT * FROM read_parquet('{path}')")
        else:
            return None
        return table
    except Exception as e:
        st.sidebar.error(f"Failed to ingest {path.name}: {e}")
        return None

def ingest_uploaded(con, uploaded_file):
    name = Path(uploaded_file.name)
    ext = name.suffix.lower()
    table = name.stem.replace(" ", "_").replace("-", "_").lower()
    
    # Save temporary file for DuckDB native scan
    temp_path = DATA_DIR / uploaded_file.name
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    try:
        if ext == ".csv":
            con.execute(f"CREATE OR REPLACE TABLE '{table}' AS SELECT * FROM read_csv_auto('{temp_path}', ignore_errors=true)")
        elif ext in (".xlsx", ".xls"):
            # Excel ingestion still requires pandas
            df = pd.read_excel(temp_path)
            con.register("_tmp_excel", df)
            con.execute(f"CREATE OR REPLACE TABLE '{table}' AS SELECT * FROM _tmp_excel")
            con.unregister("_tmp_excel")
        elif ext == ".parquet":
            con.execute(f"CREATE OR REPLACE TABLE '{table}' AS SELECT * FROM read_parquet('{temp_path}')")
        elif ext == ".json":
            con.execute(f"CREATE OR REPLACE TABLE '{table}' AS SELECT * FROM read_json_auto('{temp_path}')")
        else:
            return None
            
        # Cleanup temporary file after ingestion
        temp_path.unlink()
        return table
    except Exception as e:
        st.sidebar.error(f"Failed to load: {e}")
        if temp_path.exists(): temp_path.unlink()
        return None

def deep_clean(con, table):
    cleaned_tbl = f"{table}_cleaned"
    
    # 1. Native SQL Deduplication
    con.execute(f"CREATE OR REPLACE TABLE '{cleaned_tbl}' AS SELECT DISTINCT * FROM '{table}'")
    
    # 2. Retrieve initial column metadata
    cols_info = con.execute(f"PRAGMA table_info('{cleaned_tbl}')").fetchall()
    report = {"force_cast_cols": [], "empty_cols_names": []}
    
    # 3. SQL-based Data Healing (with SQL Safety)
    key_patterns = ["price", "qty", "amount", "total", "value", "quantity", "count", "rating"]
    
    for col_meta in cols_info:
        col_name = col_meta[1]
        col_type = col_meta[2]
        
        # Casting Logic
        if any(p in col_name.lower() for p in key_patterns) and col_type == 'VARCHAR':
            try:
                con.execute(f"""
                    UPDATE '{cleaned_tbl}' 
                    SET "{col_name}" = CAST(REPLACE(REPLACE("{col_name}", ',', ''), ' ', '') AS DOUBLE)
                    WHERE TRY_CAST(REPLACE(REPLACE("{col_name}", ',', ''), ' ', '') AS DOUBLE) IS NOT NULL
                """)
                report["force_cast_cols"].append(col_name)
            except: continue

    # 4. Actual Drop Empty Columns Logic
    for col_meta in cols_info:
        col_name = col_meta[1]
        # Check if column has 0 non-null values
        not_null_count = con.execute(f"SELECT COUNT(\"{col_name}\") FROM '{cleaned_tbl}' WHERE \"{col_name}\" IS NOT NULL").fetchone()[0]
        if not_null_count == 0:
            try:
                con.execute(f"ALTER TABLE '{cleaned_tbl}' DROP COLUMN \"{col_name}\"")
                report["empty_cols_names"].append(col_name)
            except: continue

    # Final Report Calculation
    report["rows_before"] = con.execute(f"SELECT COUNT(*) FROM '{table}'").fetchone()[0]
    report["rows_after"] = con.execute(f"SELECT COUNT(*) FROM '{cleaned_tbl}'").fetchone()[0]
    report["duplicates_removed"] = report["rows_before"] - report["rows_after"]
    report["cols_before"] = len(cols_info)
    report["cols_after"] = len(con.execute(f"PRAGMA table_info('{cleaned_tbl}')").fetchall())
    report["empty_cols_removed"] = len(report["empty_cols_names"])
    
    return cleaned_tbl, report

def list_tables(con):
    skip = {"_tmp", "_tmp_ingest", "_tmp_cleaned"}
    return [r[0] for r in con.execute("SHOW TABLES").fetchall() if r[0] not in skip]

def smart_summary(df, table_name):
    rows, cols = df.shape
    num_cols   = df.select_dtypes("number").columns.tolist()
    cat_cols   = df.select_dtypes("object").columns.tolist()
    date_cols  = df.select_dtypes("datetime").columns.tolist()
    miss_pct   = (df.isnull().sum() / rows * 100).round(1)
    dirty      = miss_pct[miss_pct > 0].sort_values(ascending=False)
    label      = "✨ Cleaned dataset" if table_name.endswith("_cleaned") else "Dataset"
    lines = [f"{label} <b>{table_name}</b> contains <b>{rows:,} rows</b> and <b>{cols} columns</b>."]
    tp = ([f"{len(num_cols)} numeric"]  if num_cols  else []) + \
         ([f"{len(cat_cols)} categorical"] if cat_cols else []) + \
         ([f"{len(date_cols)} date"] if date_cols else [])
    if tp: lines.append(f"Columns consist of: {', '.join(tp)}.")
    if dirty.empty:
        lines.append("✅ <b>No empty data</b> — the dataset is clean.")
    else:
        alerts = [f"<b>{c}</b> ({v}%)" for c, v in dirty.head(3).items()]
        lines.append(f"⚠️ <b>Dirty data detected</b> in: {', '.join(alerts)}.")
    if num_cols:
        d = df[num_cols[0]].dropna()
        if not d.empty:
            lines.append(f"Columns <b>{num_cols[0]}</b>: max <b>{d.max():,.2f}</b>, "
                         f"min <b>{d.min():,.2f}</b>, mean <b>{d.mean():,.2f}</b>.")
    if cat_cols:
        vc = df[cat_cols[0]].value_counts()
        if not vc.empty:
            lines.append(f"Dominant in <b>{cat_cols[0]}</b>: <b>{vc.idxmax()}</b> "
                         f"({vc.max():,} entries, {round(vc.max()/rows*100,1)}%).")
    if date_cols:
        d = df[date_cols[0]].dropna()
        if not d.empty:
            lines.append(f"Range: <b>{d.min().date()}</b> – <b>{d.max().date()}</b>.")
    return " ".join(lines)

def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")

def df_to_excel_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Data")
    return buf.getvalue()

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0d1828",
    font_family="Sora",
    font_color="#b8cce0",
)

with st.sidebar:
    st.markdown("## 🦆 MALLARD")
    st.caption("Local Data Warehouse · Data Healer Edition")
    st.divider()

    # ── Upload ────────────────────────────────────────────────────────────────
    st.markdown("### 📂 Data Ingestion")
    uploaded = st.file_uploader(
        "Drag & drop files here",
        type=["csv", "xlsx", "xls", "parquet", "json"],
    )
    if uploaded:
        with st.spinner(f"Loading {uploaded.name}..."):
            t = ingest_uploaded(con, uploaded)
        if t:
            st.success(f"✅ {t} loaded!")

    # ── Auto-ingest data/ folder ──────────────────────────────────────────────
    if DATA_DIR.exists():
        files = [f for f in DATA_DIR.iterdir()
                 if f.suffix.lower() in {".csv",".xlsx",".xls",".parquet",".json"}]
        for f in files:
            ingest_file(con, f)

    st.divider()

    # ── Table list ────────────────────────────────────────────────────────────
    tables   = list_tables(con)
    selected = None
    chart_type   = None
    chart_config = {}

    if tables:
        st.markdown("### 🗂️ Select Table")
        selected = st.selectbox("table", tables, label_visibility="collapsed")

        badge_html = ('<span class="badge-cleaned">✨ CLEANED</span>'
                      if selected.endswith("_cleaned")
                      else '<span class="badge-raw">📄 RAW</span>')
        st.markdown(badge_html, unsafe_allow_html=True)
        st.divider()

        # ── Data Healer ───────────────────────────────────────────────────────
        st.markdown("### 🧹 Data Refiner")
        do_clean = st.toggle("Deep Clean & Repair Data", value=False)

        if do_clean:
            cleaned_name = f"{selected}_cleaned"
            if cleaned_name in tables:
                st.info(f"Table `{cleaned_name}` already exists.")
            else:
                if st.button("▶ Execute Refinement", key=f"btn_clean_{selected}"):
                    with st.spinner("Optimizing dataset..."):
                        result_table, report = deep_clean(con, selected)
                    st.session_state["last_clean_report"] = report
                    st.session_state["last_clean_table"]  = result_table
                    st.success(f"✅ Table `{result_table}` created.")
                    st.rerun()

        st.divider()

        # ── Export (only for _cleaned) ────────────────────────────────────────
        if selected.endswith("_cleaned"):
            st.markdown("### 📤 Export Data")
            st.caption("Download processed data to local.")
            _exp_df   = con.execute(f'SELECT * FROM "{selected}"').df()
            _exp_name = selected.replace("_cleaned", "")
            
            col_csv, col_xlsx, col_pq = st.columns(3)
            with col_csv:
                st.download_button("⬇ CSV", data=df_to_csv_bytes(_exp_df), 
                                 file_name=f"{_exp_name}_refined.csv", mime="text/csv", use_container_width=True)
            with col_xlsx:
                st.download_button("⬇ Excel", data=df_to_excel_bytes(_exp_df), 
                                 file_name=f"{_exp_name}_refined.xlsx", use_container_width=True)
            with col_pq:
                buf_pq = io.BytesIO()
                _exp_df.to_parquet(buf_pq, index=False)
                st.download_button("⬇ Parquet", data=buf_pq.getvalue(), 
                                 file_name=f"{_exp_name}_refined.parquet", mime="application/octet-stream", use_container_width=True)
            st.divider()

        # ── Chart controls ────────────────────────────────────────────────────
        _df_s = con.execute(f'SELECT * FROM "{selected}"').df()
        for _c in _df_s.columns:
            if any(k in _c.lower() for k in ["date", "time", "timestamp", "year", "month"]):
                _df_s[_c] = pd.to_datetime(_df_s[_c], errors="coerce")
        _num  = _df_s.select_dtypes("number").columns.tolist()
        _cat  = _df_s.select_dtypes("object").columns.tolist()
        _date = _df_s.select_dtypes("datetime").columns.tolist()

        st.markdown("### 📊 Analytics Explorer")
        chart_type = st.selectbox("Visual Type", [
            "Auto Recommend", "Histogram", "Bar (Average)",
            "Scatter", "Line", "Box", "Correlation Heatmap"
        ], label_visibility="collapsed")

        if chart_type == "Histogram":
            chart_config["col"] = st.selectbox("Column", _num) if _num else None
        elif chart_type == "Bar (Average)":
            chart_config["x"]     = st.selectbox("Category (X)", _cat) if _cat else None
            chart_config["y"]     = st.selectbox("Value (Y)", _num) if _num else None
            chart_config["top_n"] = st.slider("Top N", 5, 30, 15)
        elif chart_type == "Scatter":
            chart_config["x"]     = st.selectbox("Column X", _num) if _num else None
            chart_config["y"]     = st.selectbox("Column Y", _num,
                                        index=min(1, len(_num)-1)) if len(_num) > 1 else None
            chart_config["color"] = st.selectbox("Color", ["—"] + _cat)
        elif chart_type == "Line":
            _all_x = _date + _num + _cat
            chart_config["x"]     = st.selectbox("Column X", _all_x) if _all_x else None
            chart_config["y"]     = st.selectbox("Column Y", _num) if _num else None
            chart_config["color"] = st.selectbox("Color", ["—"] + _cat)
        elif chart_type == "Box":
            chart_config["x"] = st.selectbox("Category (X)", ["—"] + _cat)
            chart_config["y"] = st.selectbox("Value (Y)", _num) if _num else None

    # ── DB footer ─────────────────────────────────────────────────────────────
    st.divider()
    st.markdown(
        f"<small style='font-family:JetBrains Mono,monospace;color:#2d4a6a'>"
        f"DB · {DB_PATH} | {len(tables) if tables else 0} table(s)<br>"
        f"<span style='color:#16a34a'>● CONNECTION ACTIVE</span></small>",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# MAIN AREA
# ══════════════════════════════════════════════════════════════════════════════

# Welcome screen
if not tables or selected is None:
    st.markdown("""
    <div class="welcome-wrap">
        <div class="welcome-duck">🦆</div>
        <div class="welcome-title">MALLARD</div>
        <div class="welcome-sub">Local Data Warehouse &nbsp;·&nbsp; Data Refiner Edition</div>
        <div class="step-grid">
            <div class="step-card">
                <div class="step-num">Step 01</div>
                <div class="step-icon">📂</div>
                <div class="step-title">Data Ingestion</div>
                <div class="step-desc">Ingest CSV, Excel, Parquet, or JSON via the sidebar to initialize your local warehouse.</div>
            </div>
            <div class="step-card">
                <div class="step-num">Step 02</div>
                <div class="step-icon">🧹</div>
                <div class="step-title">Clean & Refine</div>
                <div class="step-desc">Enable Deep Refiner to optimize data types, drop duplicates, and repair schema inconsistencies automatically.</div>
            </div>
            <div class="step-card">
                <div class="step-num">Step 03</div>
                <div class="step-icon">📊</div>
                <div class="step-title">Analyze & Export</div>
                <div class="step-desc">Visualize trends using Automated Insights, then export your refined datasets to CSV or Excel.</div>
            </div>
        </div>
        <div class="fmt-label">Supported · CSV · XLSX · XLS · PARQUET · JSON</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Load df
df = con.execute(f'SELECT * FROM "{selected}" LIMIT 1000').df()
for col in df.columns:
    if any(k in col.lower() for k in ["date", "time", "timestamp", "year", "month"]):
        df[col] = pd.to_datetime(df[col], errors="coerce")

num_cols  = df.select_dtypes("number").columns.tolist()
cat_cols  = df.select_dtypes("object").columns.tolist()
date_cols = df.select_dtypes("datetime").columns.tolist()

# Header
badge = ('<span class="badge-cleaned">✨ CLEANED</span>' if selected.endswith("_cleaned")
         else '<span class="badge-raw">📄 RAW</span>')
st.markdown(f"# {selected.replace('_',' ').title()} &nbsp; {badge}", unsafe_allow_html=True)

# Cleaning log
if "last_clean_report" in st.session_state and "last_clean_table" in st.session_state:
    if st.session_state["last_clean_table"].startswith(selected.replace("_cleaned", "")):
        r = st.session_state["last_clean_report"]

        def _tags(cols):
            if not cols:
                return '<span style="color:#5a7a9a;font-style:italic;font-size:0.82rem">—</span>'
            return " ".join(f'<span class="col-tag">{c}</span>' for c in cols)

        st.markdown(f"""
        <div class="clean-box">
        ✅ <b>Deep Clean successful.</b><br><br>
        <b>📊 Execution Summary</b><br>
        &nbsp;&nbsp;🗑️ Duplicates removed: <b>{r['duplicates_removed']:,} Rows</b><br>
        &nbsp;&nbsp;📭 Empty columns dropped: <b>{r['empty_cols_removed']}</b><br>
        &nbsp;&nbsp;📈 Rows <b>{r['rows_before']:,}</b> → <b>{r['rows_after']:,}</b>
        &nbsp;|&nbsp; Columns <b>{r['cols_before']}</b> → <b>{r['cols_after']}</b><br><br>
        <b>🩺 Columns that were healed</b><br>
        <span style="font-size:0.8rem;color:#5a7a9a">Force-cast (key name)</span><br>
        {_tags(r.get('force_cast_cols',[]))}<br><br>
        <span style="font-size:0.8rem;color:#5a7a9a">Auto-inferred to numeric</span><br>
        {_tags(r.get('inferred_numeric_cols',[]))}<br><br>
        <span style="font-size:0.8rem;color:#5a7a9a">Empty columns dropped</span><br>
        {_tags(r.get('empty_cols_names',[]))}
        </div>
        """, unsafe_allow_html=True)

# Metrics
total_rows = con.execute(f'SELECT COUNT(*) FROM "{selected}"').fetchone()[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rows",        f"{total_rows:,}") 
c2.metric("Columns",     len(df.columns))
c3.metric("Numeric",     len(num_cols))
c4.metric("Categorical", len(cat_cols))
c5.metric("Size",        f"{df.memory_usage(deep=True).sum()/1e6:.2f} MB")
st.divider()

# Smart Summary
st.markdown("### 🧠 Automated Insights")
st.markdown(f'<div class="summary-box">{smart_summary(df, selected)}</div>',
            unsafe_allow_html=True)

if not num_cols and not selected.endswith("_cleaned"):
    st.markdown("""
    <div class="warn-box">
    ⚠️ <b>No numeric columns. Run Deep Clean first.</b>
    Enable <b>🧹 Deep Refiner & Repair Data</b> in the sidebar.
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Data Preview
st.markdown("### 🔍 Data Preview")
with st.expander("📋 Schema & Type Validation"):
    schema_info = con.execute(f"PRAGMA table_info('{selected}')").df()
    st.table(schema_info[['name', 'type']])
    st.caption("Verify schema and data types (VARCHAR, DOUBLE, BIGINT, etc.)")
st.dataframe(df.head(100), use_container_width=True)
st.divider()

# Data Visualization
st.markdown("### 📊 Data Visualization")

if not num_cols and chart_type not in ["Bar (Average)", "Auto Recommend"]:
    st.info("Not enough compatible data types for recommendations. Run Deep Refiner first.")
else:
    if chart_type == "Auto Recommend":
        rendered = 0
        if num_cols:
            st.markdown(f"**💡 Recommendation #1 — Distribution `{num_cols[0]}`**")
            fig = px.histogram(df, x=num_cols[0], nbins=40,
                               title=f"Distribution — {num_cols[0]}",
                               template="plotly_dark",
                               color_discrete_sequence=["#3b82f6"])
            fig.update_layout(**PLOTLY_THEME)
            st.plotly_chart(fig, use_container_width=True)
            rendered += 1
        if cat_cols and num_cols:
            st.markdown(f"**💡 Recommendation #2 — Average `{num_cols[0]}` per `{cat_cols[0]}`**")
            grp = df.groupby(cat_cols[0])[num_cols[0]].mean().nlargest(15).reset_index()
            fig = px.bar(grp, x=cat_cols[0], y=num_cols[0],
                         title=f"Average {num_cols[0]} per {cat_cols[0]} (Top 15)",
                         template="plotly_dark",
                         color_discrete_sequence=["#10b981"])
            fig.update_layout(**PLOTLY_THEME)
            st.plotly_chart(fig, use_container_width=True)
            rendered += 1
        if len(num_cols) >= 4:
            st.markdown("**💡 Recommendation #3 — Correlation Heatmap**")
            corr = df[num_cols[:10]].corr().round(2)
            fig  = px.imshow(corr, text_auto=True, title="Correlation Heatmap",
                             template="plotly_dark", color_continuous_scale="Blues")
            fig.update_layout(**PLOTLY_THEME)
            st.plotly_chart(fig, use_container_width=True)
            rendered += 1
        if rendered == 0:
            st.info("Insufficient data types for recommendations. Run Deep Refiner first.")
    else:
        fig = None
        if chart_type == "Histogram" and chart_config.get("col"):
            fig = px.histogram(df, x=chart_config["col"], nbins=40,
                               title=f"Distribution — {chart_config['col']}",
                               template="plotly_dark", color_discrete_sequence=["#3b82f6"])
        elif chart_type == "Bar (Average)" and chart_config.get("x") and chart_config.get("y"):
            grp = df.groupby(chart_config["x"])[chart_config["y"]].mean() \
                    .nlargest(chart_config["top_n"]).reset_index()
            fig = px.bar(grp, x=chart_config["x"], y=chart_config["y"],
                         title=f"Average {chart_config['y']} per {chart_config['x']}",
                         template="plotly_dark", color_discrete_sequence=["#3b82f6"])
        elif chart_type == "Scatter" and chart_config.get("x") and chart_config.get("y"):
            fig = px.scatter(df, x=chart_config["x"], y=chart_config["y"],
                             color=None if chart_config["color"] == "—" else chart_config["color"],
                             title=f"{chart_config['x']} vs {chart_config['y']}",
                             template="plotly_dark", opacity=0.7)
        elif chart_type == "Line" and chart_config.get("x") and chart_config.get("y"):
            fig = px.line(df.sort_values(chart_config["x"]),
                          x=chart_config["x"], y=chart_config["y"],
                          color=None if chart_config["color"] == "—" else chart_config["color"],
                          title=f"{chart_config['y']} over {chart_config['x']}",
                          template="plotly_dark")
        elif chart_type == "Box" and chart_config.get("y"):
            fig = px.box(df,
                         x=None if chart_config.get("x") == "—" else chart_config.get("x"),
                         y=chart_config["y"],
                         title=f"Box Plot — {chart_config['y']}",
                         template="plotly_dark", color_discrete_sequence=["#3b82f6"])
        elif chart_type == "Correlation Heatmap":
            if len(num_cols) >= 2:
                corr = df[num_cols].corr().round(2)
                fig  = px.imshow(corr, text_auto=True, title="Correlation Heatmap",
                                 template="plotly_dark", color_continuous_scale="Blues")
            else:
                st.info("Minimum 2 numeric columns for heatmap.")
        if fig:
            fig.update_layout(**PLOTLY_THEME)
            st.plotly_chart(fig, use_container_width=True)

st.divider()

with st.expander("📈 Descriptive Statistics"):
    st.dataframe(df.describe(include="all").T, use_container_width=True)

with st.expander("🛠️ Power User — Custom SQL"):
    sql = st.text_area("SQL Query:", value=f'SELECT * FROM "{selected}" LIMIT 50', height=120)
    if st.button("▶ Run Query", key="btn_run_sql"):
        try:
            result = con.execute(sql).df()
            st.dataframe(result, use_container_width=True)
            st.caption(f"{len(result):,} rows returned")
            col_csv, col_xlsx, col_pq = st.columns(3)
            with col_csv:
                st.download_button("⬇ CSV", data=df_to_csv_bytes(result),
                                 file_name="query_result.csv", mime="text/csv", use_container_width=True)
            with col_xlsx:
                st.download_button("⬇ Excel", data=df_to_excel_bytes(result),
                                 file_name="query_result.xlsx", use_container_width=True)
            with col_pq:
                buf_pq = io.BytesIO()
                result.to_parquet(buf_pq, index=False)
                st.download_button("⬇ Parquet", data=buf_pq.getvalue(),
                                 file_name="query_result.parquet", mime="application/octet-stream", use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.caption("🦆 MALLARD · Data Refiner Edition · DuckDB + Streamlit · 100% Local & Free")