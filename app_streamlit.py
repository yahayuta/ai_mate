import streamlit as st
import json
import os
import model_chat_log

st.set_page_config(page_title="AI Mate Admin", layout="wide", page_icon="✨")

st.title('✨ AI Mate Dashboard')
st.markdown("Manage your AI Mate's personality and view chat history analytics.")

# --- Personality Settings ---
st.sidebar.header("🧠 Persona Settings")
persona_file = "persona.json"

# Load current persona
default_persona = "あなたは人間なので口語で会話してください"
if os.path.exists(persona_file):
    try:
        with open(persona_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            current_persona = data.get("system_prompt", default_persona)
    except:
        current_persona = default_persona
else:
    current_persona = default_persona

# Persona UI
new_persona = st.sidebar.text_area("System Prompt", value=current_persona, height=150)
st.sidebar.caption("This completely overrides the backend instructions for how the AI Mate speaks.")

if st.sidebar.button("💾 Save Persona", use_container_width=True):
    with open(persona_file, "w", encoding="utf-8") as f:
        json.dump({"system_prompt": new_persona}, f, ensure_ascii=False)
    st.sidebar.success("Persona saved successfully!")

# --- Chat Logs ---
st.header("💬 Chat History")

col1, col2 = st.columns([8, 2])
with col1:
    st.markdown("View all conversations stored in Google BigQuery.")
with col2:
    if st.button("🗑️ Clear Logs", type="primary", use_container_width=True):
        model_chat_log.delete_logs()
        st.success("Logs cleared!")
        st.rerun()

st.divider()

# Fetch Logs
try:
    with st.spinner("Fetching BigQuery records..."):
        logs = model_chat_log.get_logs()
        
    if not logs:
        st.info("No chat logs found in BigQuery.")
    else:
        for log in logs:
            if log["role"] == "user":
                with st.chat_message("user", avatar="🧑‍💻"):
                    st.write(log["content"])
            else:
                with st.chat_message("assistant", avatar="✨"):
                    st.write(log["content"])
except Exception as e:
    st.error(f"Failed to fetch logs: {e}")
