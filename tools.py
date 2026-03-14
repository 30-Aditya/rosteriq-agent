VERSION = "1.2 (STABLE)"
import os
import plotly.express as px
from langchain.tools import tool

from langchain_community.tools import DuckDuckGoSearchRun

# Using global instance with absolute paths for robustness
from data_engine import DataEngine
base_dir = os.path.dirname(os.path.abspath(__file__))
engine = DataEngine(
    os.path.join(base_dir, "roster_processing_details.csv"), 
    os.path.join(base_dir, "aggregated_operational_metrics.csv")
)

@tool
def web_search_tool(query: str) -> str:
    """Useful for fetching external regulatory context, CMS rules, or provider org business info."""
    search = DuckDuckGoSearchRun()
    return search.run(query)

def _safe_df_check(df):
    """Internal helper to safely check if engine result is a valid non-empty DataFrame."""
    if isinstance(df, str):
        return False, f"Engine Error: {df}"
    if df is None or not hasattr(df, "empty"):
        return False, f"Engine Error: Unexpected return type {type(df)}"
    if df.empty:
        return False, "No data found for this request."
    return True, df

@tool
def query_duckdb_tool(sql_query: str) -> str:
    """Executes a SQL query against RosterIQ datasets. Results are optimized for UI display."""
    df = engine.query(sql_query)
    if isinstance(df, str): return df
    
    # UI Optimization: Keep only operational columns if too many
    if len(df.columns) > 5:
        keep = ['ro_id', 'org_nm', 'latest_stage_nm', 'total_duration', 'cnt_state', 'scs_percent']
        actual_keep = [c for c in keep if c in df.columns]
        if actual_keep:
            df = df[actual_keep]

    return df.to_markdown(index=False)

@tool
def triage_stuck_ros() -> str:
    """Identify and summarize stuck roster operations locally. No input parameters required."""
    is_ok, result = _safe_df_check(engine.query("SELECT ro_id, org_nm, cnt_state, latest_stage_nm, total_duration FROM roster_diagnosis_view WHERE operational_status = 'Stuck' ORDER BY total_duration DESC LIMIT 10"))
    if not is_ok: return result
    
    summary = f"### Stuck Roster Operations Triage (V1.2)\nDetected {len(result)} stuck operations.\n\n"
    summary += result.to_markdown(index=False)
    summary += "\n\n**Action**: Investigate bottlenecks in Mapping Approval and DART stages."
    return summary

@tool
def market_health_report(market: str = None) -> str:
    """Combines pipeline and market data for health reporting. Parameter: 'market' (state abbreviation)."""
    filter_clause = f"WHERE market = '{market}'" if market else ""
    query = f"SELECT m.market, AVG(m.scs_percent) as avg_scs, COUNT(r.ro_id) as total_ro, SUM(CASE WHEN r.is_stuck = 1 THEN 1 ELSE 0 END) as stuck_count FROM aggregated_operational_metrics m LEFT JOIN roster_processing_details r ON m.market = r.cnt_state {filter_clause} GROUP BY m.market ORDER BY avg_scs ASC"
    is_ok, result = _safe_df_check(engine.query(query))
    if not is_ok: return result
    return f"### Market Health Summary (V1.2)\n" + result.to_markdown(index=False)

@tool
def generate_stuck_ro_viz() -> str:
    """Generates a bar chart of stuck roster operations by market. No input parameters required."""
    is_ok, result = _safe_df_check(engine.query("SELECT cnt_state as Market, COUNT(*) as Count FROM roster_processing_details WHERE is_stuck = 1 GROUP BY cnt_state"))
    if not is_ok: return result
    fig = px.bar(result, x='Market', y='Count', title="Stuck Roster Operations by Market (V1.2)")
    return fig.to_json()

@tool
def generate_success_trend_viz() -> str:
    """Generates a line chart for Market Success Rate trends. No input parameters required."""
    is_ok, result = _safe_df_check(engine.query("SELECT _month as Month, AVG(scs_percent) as Avg_Success FROM aggregated_operational_metrics GROUP BY _month ORDER BY _month"))
    if not is_ok: return result
    fig = px.line(result, x='Month', y='Avg_Success', title="Success Rate Trends (V1.2)")
    return fig.to_json()

@tool
def generate_retry_effectiveness_viz() -> str:
    """Generates a visualization showing retry success. No input parameters required."""
    is_ok, result = _safe_df_check(engine.query("SELECT market, AVG(scs_percent) as rate FROM aggregated_operational_metrics GROUP BY market"))
    if not is_ok: return result
    fig = px.bar(result, x='market', y='rate', title="Retry Recovery Power (V1.2)")
    return fig.to_json()

@tool
def generate_pipeline_health_report(state: str) -> str:
    """Generates a Pipeline Health Report for a specific state. Parameter: 'state'."""
    m_ok, m_res = _safe_df_check(engine.query(f"SELECT AVG(scs_percent) as s FROM aggregated_operational_metrics WHERE market = '{state}'"))
    s_ok, s_res = _safe_df_check(engine.query(f"SELECT COUNT(*) as c FROM roster_processing_details WHERE cnt_state = '{state}' AND is_stuck = 1"))
    
    m_str = f"{m_res.iloc[0,0]:.2f}%" if m_ok and m_res.iloc[0,0] is not None else "N/A"
    s_str = str(s_res.iloc[0,0]) if s_ok else "0"
    
    return f"Report for {state} (V1.2): Success {m_str}, Stuck {s_str}."
