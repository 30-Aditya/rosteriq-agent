import pandas as pd
import duckdb
import os

class DataEngine:
    def __init__(self, roster_csv_path, metrics_csv_path):
        self.roster_csv_path = roster_csv_path
        self.metrics_csv_path = metrics_csv_path
        self.conn = duckdb.connect(database=':memory:')
        self._load_data()

    def _load_data(self):
        """Loads and prepares the CSV files into DuckDB for fast querying."""
        # Use absolute paths and escape single quotes for SQL string safety
        roster_path = os.path.abspath(self.roster_csv_path).replace("'", "''")
        metrics_path = os.path.abspath(self.metrics_csv_path).replace("'", "''")
        
        query = f"""
            CREATE OR REPLACE VIEW roster_processing_details AS SELECT * FROM read_csv_auto('{roster_path}', normalize_names=True);
            CREATE OR REPLACE VIEW aggregated_operational_metrics AS SELECT * FROM read_csv_auto('{metrics_path}', normalize_names=True);
            
            -- Specialized view for rapid diagnosis
            CREATE OR REPLACE VIEW roster_diagnosis_view AS
            SELECT 
                r.*,
                (COALESCE(pre_processing_duration, 0) + COALESCE(mapping_aproval_duration, 0) + COALESCE(isf_gen_duration, 0) + COALESCE(dart_gen_duration, 0) + COALESCE(dart_review_duration, 0) + COALESCE(dart_ui_validation_duration, 0) + COALESCE(sps_load_duration, 0)) as total_duration,
                CASE WHEN is_failed = 1 THEN 'Failed' WHEN is_stuck = 1 THEN 'Stuck' ELSE 'Processing' END as operational_status
            FROM roster_processing_details r;
        """
        self.conn.execute(query)
        
    def query(self, sql_query):
        """Execute a raw SQL query against the loaded data."""
        try:
            return self.conn.execute(sql_query).fetchdf()
        except Exception as e:
            return f"Error executing query: {str(e)}"
            
    def get_stuck_ros(self):
        """Standard procedure utility: returns stuck RO details."""
        return self.query("SELECT ro_id, org_nm, cnt_state, latest_stage_nm, file_status_cd FROM roster_diagnosis_view WHERE is_stuck = 1 ORDER BY total_duration DESC LIMIT 50")
        
    def get_market_health(self, state):
        """Standard procedure utility: merges market metrics with pipeline health."""
        query = f"""
            SELECT 
                m.month, m.market, m.scs_percent, m.overall_fail_cnt,
                COUNT(r.ro_id) as total_ros_processed,
                SUM(CASE WHEN r.is_failed = 1 THEN 1 ELSE 0 END) as failed_ros,
                SUM(CASE WHEN r.is_stuck = 1 THEN 1 ELSE 0 END) as stuck_ros
            FROM aggregated_operational_metrics m
            LEFT JOIN roster_processing_details r ON m.market = r.cnt_state
            WHERE m.market = '{state}'
            GROUP BY m.month, m.market, m.scs_percent, m.overall_fail_cnt
        """
        return self.query(query)
