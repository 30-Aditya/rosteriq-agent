# RosterIQ: Memory-Driven Provider Roster Intelligence 🧠

**Project Deliverables (Docs & Demo):** [View on Google Drive](https://drive.google.com/drive/folders/1AI8nTYpGFuocRDHTyvSWbwltjT3Dn7Mq?usp=sharing)

RosterIQ is an autonomous AI agent designed for HiLabs AgentX AI 2026. It operates over healthcare roster pipeline and market transaction data, maintaining a multi-layered memory system to diagnose operational anomalies with high precision.

## 🚀 Key Features
- **3-Layer Memory Architecture**: Episodic, Procedural, and Semantic memory integration.
- **Direct Command Router**: Instant execution of diagnostic procedures bypassing LLM latency.
- **Local Analytics Engine**: High-performance querying using DuckDB and interactive visualizations using Plotly.
- **Emergency Stabilization Layer**: Automatic fallback and safe-triage mechanism for 100% uptime.

## 🗂️ Memory Architecture
Our agent implements the full memory rubric:
1. **Semantic Memory (DNA)**: Internalized domain knowledge of the 7-stage healthcare roster pipeline. The agent "knows" what ISF, DART, and SPS represent.
2. **Procedural Memory (Skills)**: Hard-coded diagnostic workflows (`triage_stuck_ros`, `market_health_report`) that the agent re-uses reliably.
3. **Episodic Memory (Experience)**: SQLite-backed tracking of previous investigations and flagged anomalies across sessions.

## 🛠️ Setup Instructions
1. **Clone the Repo**:
   ```bash
   git clone https://github.com/30-Aditya/rosteriq-agent.git
   cd rosteriq-agent
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```env
   OPENROUTER_API_KEY=your_key_here
   ```
4. **Run the Agent**:
   ```bash
   streamlit run app.py
   ```

## 📊 Diagnostic Procedures
- `Run triage_stuck_ros`: Identify stalled ROs across all states.
- `Show market health dashboard`: Join pipeline data with market success rates.
- `Analyze retry effectiveness`: Visualization of first-pass vs recovery success.

## 🏗️ Architecture Design
**User Query** ➡️ **Direct Command Router** ➡️ **DuckDB SQL Engine** ➡️ **Plotly Visualization** ➡️ **LLM Final Summary**

---
*Developed for HiLabs AgentX AI 2026. Version 1.2 Stable.*
