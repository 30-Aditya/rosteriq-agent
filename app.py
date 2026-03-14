import streamlit as st
import os
import json
import plotly.io as pio
from dotenv import load_dotenv

# Try to import agent, if it handles environment errors it will throw them early
try:
    from agent import RosterAgent
    import tools
    TOOLS_VERSION = getattr(tools, "VERSION", "Unknown")
except ImportError:
    RosterAgent = None
    TOOLS_VERSION = "N/A"

# Ensure environment variables are loaded if .env exists
load_dotenv()

def main():
    st.set_page_config(page_title="RosterIQ Agent", page_icon="🧠", layout="wide")
    st.title("RosterIQ: Memory-Driven Intelligence Agent 🧠")
    
    st.sidebar.header("Configuration")
    st.sidebar.info(f"🛠️ Tools Version: {TOOLS_VERSION}")
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    api_key = st.sidebar.text_input("🔑 OpenRouter API Key", value=openrouter_key, type="password")
    
    if api_key:
        os.environ["OPENROUTER_API_KEY"] = api_key
        if not openrouter_key:
            st.sidebar.success("✅ OpenRouter Key Loaded!")
            
    st.sidebar.markdown("---")
    st.sidebar.subheader("Memory State")
    st.sidebar.markdown("🗂️ Episodic Memory: **Active**")
    st.sidebar.markdown("⚙️ Procedural Memory: **Active**")
    st.sidebar.markdown("🧬 Semantic Memory: **Active**")
    
    if st.sidebar.button("🔄 Reset Agent & Memory"):
        st.session_state.clear()
        st.rerun()
    
    # Initialize the Agent in session state so it remembers memory layers correctly
    if "roster_agent" not in st.session_state:
        if api_key:
            try:
                st.session_state.roster_agent = RosterAgent()
            except Exception as e:
                st.sidebar.error(f"Error starting agent: {str(e)}")
                st.session_state.roster_agent = None
        else:
            st.session_state.roster_agent = None

    st.markdown("### Chat Interface")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Welcome to RosterIQ! I am connected to the RO Pipeline and Market Metrics layers. Ask me to triage stuck files, fetch memory patterns, or run cross-market diagnosis."}]
        
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # If the content is likely a JSON chart (Plotly), render it
            if "data" in message.get("plot_data", ""):
                 fig = pio.from_json(message["plot_data"])
                 st.plotly_chart(fig, use_container_width=True)
            
    if prompt := st.chat_input("Ask RosterIQ about pipeline status or market metrics..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            if not st.session_state.roster_agent:
                st.error("Please configure the Gemini API Key in the sidebar to initialize RosterIQ.")
            else:
                with st.spinner("Accessing pipelines and memory..."):
                    response = st.session_state.roster_agent.run(prompt)
                    
                    # Very rudamentary check to see if the LLM outputted a JSON plotly string explicitly 
                    # In a robust scenario, we would parse structured tool output, but here we just check strings
                    plot_json_str = ""
                    if '{"data":' in response and 'layout' in response:
                         try:
                             # Extract just the json portion assuming it got wrapped in code blocks or dumped
                             json_start = response.find('{"data":')
                             json_end = response.rfind('}') + 1
                             plot_json_str = response[json_start:json_end]
                             
                             # strip it out of the main response so we render text cleanly
                             response = response[:json_start] + f"\\n*(Generated interactive chart below)*"
                             
                             fig = pio.from_json(plot_json_str)
                             st.markdown(response)
                             st.plotly_chart(fig, use_container_width=True)
                         except:
                             st.markdown(response)
                    else:
                         st.markdown(response)
                         
                st.session_state.messages.append({"role": "assistant", "content": response, "plot_data": plot_json_str})

if __name__ == "__main__":
    main()