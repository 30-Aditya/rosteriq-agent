import sqlite3
import datetime

class MemoryLayer:
    """Manages Episodic, Procedural, and Semantic memory for RosterIQ."""
    def __init__(self, db_path="roster_iq_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the SQLite database for Episodic Memory persistence."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversation_history 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      timestamp TEXT, 
                      role TEXT, 
                      content TEXT,
                      topic_tags TEXT)''')
        conn.commit()
        conn.close()

    # --- 1. Episodic Memory ---
    def save_interaction(self, role, content, tags=""):
        """Saves a conversation turn to the database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO conversation_history (timestamp, role, content, topic_tags) VALUES (?, ?, ?, ?)",
                  (datetime.datetime.now().isoformat(), role, content, tags))
        conn.commit()
        conn.close()

    def get_recent_context(self, limit=10):
        """Retrieves exactly what happened previously to detect state changes."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT role, content FROM conversation_history ORDER BY id DESC LIMIT ?", (limit,))
        history = c.fetchall()
        conn.close()
        return [{"role": r, "content": c} for r, c in reversed(history)]

    # --- 2. Procedural Memory ---
    def get_procedures(self):
        """Returns standard operating procedures for the agent to execute on demand."""
        return {
            "triage_stuck_ros": """
                1. Call DataEngine.get_stuck_ros()
                2. Rank results by time stuck (total_duration)
                3. Check health flags (if Red -> Critical priority)
                4. Recommend escalation actions to user.
            """,
            "market_health_report": """
                1. Identify target state/market.
                2. Call DataEngine.get_market_health(state).
                3. Analyze mapping of pipeline stuck/failed to total transaction market percentage.
                4. Output structured analysis using Visualization tools.
            """,
            "retry_effectiveness_analysis": """
                1. Connect to aggregated_operational_metrics.
                2. Calculate metrics: (NEXT_ITER_SCS_CNT / (FIRST_ITER_FAIL_CNT + NEXT_ITER_SCS_CNT)) * 100
                3. Determine if reprocessing adds excessive latency using roster_processing_details average duration.
            """
        }

    # --- 3. Semantic Memory ---
    def get_domain_knowledge(self):
        """Returns operational glossary and concept mapping."""
        return {
            "LOB": "Line of Business. Examples: Medicare HMO, Medicaid FFS, Commercial PPO",
            "SCS_PERCENT": "Overall transaction success rate (%). Target threshold is usually 95%. Drops below this indicate market-wide failures.",
            "IS_STUCK": "RO is delayed in current stage vs historical benchmark. Not necessarily failed yet.",
            "IS_FAILED": "RO encountered a fatal error (e.g. Complete Validation Failure) and dropped out of the pipeline.",
            "FILE_STATUS_CD": {
                "9": "Stopped/Failed",
                "23": "Pre-processing",
                "45": "DART Review",
                "49": "DART Generation",
                "65": "SPS Load",
                "99": "Resolved/Completed"
            }
        }
