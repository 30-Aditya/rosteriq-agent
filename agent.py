import os
import re
import json
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage
from memory_layer import MemoryLayer
from tools import (query_duckdb_tool, triage_stuck_ros, market_health_report,
                   generate_stuck_ro_viz, generate_success_trend_viz, 
                   generate_retry_effectiveness_viz, web_search_tool)

load_dotenv()

SYSTEM_CONTEXT = """You are RosterIQ, an autonomous AI agent for healthcare roster pipeline operations.

--- SEMANTIC MEMORY (DOMAIN KNOWLEDGE) ---
PIPELINE STAGES:
1. Ingestion: Initial file receipt.
2. Pre-processing: Data cleanup and formatting.
3. Mapping Approval: Validating field mappings.
4. ISF Generation: Creating Intermediate Standard Format.
5. DART Generation: Processing records through business rules.
6. DART UI Validation: Manual or automated review of DART results.
7. SPS Load: Final data loading into the core system.

HEALTH FLAGS:
- Green: Stage completed within historical average duration.
- Yellow: Duration exceeds historical average (Potential Bottleneck).
- Red: Stage has failed or critical error detected.

OPERATIONAL STATES:
- IS_STUCK: Boolean. The RO is stalled in a stage (active but not moving).
- IS_FAILED: Boolean. The RO has encountered a terminal error.

BUSINESS CONTEXT:
- LOBs: Medicare HMO, Medicaid FFS, Commercial PPO/EPO, etc.
- Source Systems: AvailityPDM, Demographic, ProviderGroup.

--- WORKFLOW & TOOLS ---
1. Use web_search_tool logic for external context (CMS rules, regulatory shifts, provider org info).
2. Use local procedure tools for direct commands:
   - "Run triage_stuck_ros" -> Identify logic for stuck ROs.
   - "Analyze retry effectiveness" -> Use generate_retry_effectiveness_viz.
   - "Show market health dashboard" -> Use market_health_report.
3. Use query_duckdb_tool for general SQL joins & data mining.

STRICT RULE: Local SQL -> Local Chart -> LLM Explanation. DO NOT dump raw CSV rows.
"""

class RosterAgent:
    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")
            
        self.llm = ChatOpenAI(
            model="mistralai/mistral-7b-instruct",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.1,
            max_retries=1
        )
        
        self.memory_system = MemoryLayer()
        self.tool_map = {
            "query_duckdb_tool": query_duckdb_tool,
            "triage_stuck_ros": triage_stuck_ros,
            "market_health_report": market_health_report,
            "generate_stuck_ro_viz": generate_stuck_ro_viz,
            "generate_success_trend_viz": generate_success_trend_viz,
            "generate_retry_effectiveness_viz": generate_retry_effectiveness_viz,
            "web_search_tool": web_search_tool
        }

    def _call_tool(self, tool_name: str, tool_args: dict) -> str:
        tool = self.tool_map.get(tool_name)
        if not tool: return f"Unknown tool: {tool_name}"
        try:
            return str(tool.invoke(tool_args))
        except Exception as e:
            return f"Tool Error: {str(e)}"

    def run(self, user_input: str) -> str:
        # --- Direct Command Router (Bypasses LLM for speed/reliability) ---
        input_lower = user_input.lower()
        if "triage_stuck_ros" in input_lower or "run triage" in input_lower:
            return self._call_tool("triage_stuck_ros", {})
        if "stuck roster operations" in input_lower and "visualize" in input_lower:
            return self._call_tool("generate_stuck_ro_viz", {})
        if "market health" in input_lower or "health dashboard" in input_lower:
            # Extract state if present (simple regex)
            state_match = re.search(r"for\s+([a-zA-Z\s]+)", input_lower)
            state = state_match.group(1).title() if state_match else None
            return self._call_tool("market_health_report", {"market": state})
        if "success rate trend" in input_lower:
            return self._call_tool("generate_success_trend_viz", {})
        if "retry effectiveness" in input_lower:
            return self._call_tool("generate_retry_effectiveness_viz", {})

        # --- LLM Processing with Fallback ---
        past_context = self.memory_system.get_recent_context(limit=3)
        context_str = "\n".join([f"{m['role']}: {m['content']}" for m in past_context])
        
        prompt = (
            f"{SYSTEM_CONTEXT}\n\nContext:\n{context_str}\n\n"
            f"Question: {user_input}\n\n"
            "Return JSON: {\"action\": \"tool_name\", \"action_input\": {...}} or {\"action\": \"Final Answer\", \"action_input\": \"...\"}"
        )
        
        conversation = [HumanMessage(content=prompt)]
        
        try:
            for _ in range(5):
                response = self.llm.invoke(conversation)
                raw = response.content.strip()
                if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
                
                try:
                    parsed = json.loads(raw)
                    action = parsed.get("action")
                    action_input = parsed.get("action_input", {})
                    
                    if action == "Final Answer":
                        ans = str(action_input)
                        self.memory_system.save_interaction("user", user_input)
                        self.memory_system.save_interaction("assistant", ans)
                        return ans
                    
                    res = self._call_tool(action, action_input)
                    conversation.append(HumanMessage(content=f"Tool result: {res}\nProvide final summary or next action."))
                except:
                    # If LLM returns non-JSON or weird output, return it directly
                    return raw
        except Exception as e:
            # --- LLM Fallback: If API fails, try to fulfill via SQL tool directly ---
            fallback_res = self._call_tool("query_duckdb_tool", {"sql_query": "SELECT ro_id, org_nm, latest_stage_nm, total_duration FROM roster_diagnosis_view LIMIT 5"})
            return f"Note: LLM currently unavailable. Direct Data Result (Diagnostic View):\n\n{fallback_res}"

        return "Agent encountered an error. Please try a direct command."
