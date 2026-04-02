import asyncio
from dotenv import load_dotenv
import os
import streamlit as st

def init_session_state():
    """Initialize session state with default values. This should be called prior to accessing any session state variables."""
    load_dotenv()
    default_state = {
        "messages": [],
        "mcp_json": {},
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/"),
        "system_prompt": (
            "You are a helpful assistant that can understand both text and images. Answer the user's questions "
            "thoroughly but concisely, and use web search tools to obtain the most up-to-date information if necessary."
        ),
        "thread_id": 1,
        "stream_mode": "values",
    }
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value

async def main():
    st.set_page_config(page_title="MCP Travel Agent", page_icon=":llama:",
                       initial_sidebar_state="collapsed")
    init_session_state()

    st.title("MCP Travel Agent")

if __name__ == "__main__":
    asyncio.run(main())
