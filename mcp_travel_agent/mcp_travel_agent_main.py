import asyncio
from dotenv import load_dotenv
import os
from st_chat_input_multimodal import multimodal_chat_input
import streamlit as st
from utils import *

def init_session_state():
    """Initialize session state with default values. This should be called prior to accessing any session state variables."""
    load_dotenv()
    default_state = {
        "messages": [],
        "mcp_json": """
        {
            "travel_server": {
                "transport": "streamable_http",
                "url": "https://mcp.kiwi.com"
            },
            "exchange_rate_server": {
                "transport": "streamable_http",
                "url": "http://localhost:8000/mcp"
            }
        }
        """,
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/"),
        "system_prompt": (
            "You are a travel agent who uses your tools to help the user find flights. "
            "Whenever the user asks for a flight, find the cheapest flights and provide the details. "
            "Do NOT book flights. Also, provide the prices in USD."
        ),
        "thread_id": 1,
        "stream_mode": "values",
    }
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value
    st.session_state["models"] = get_models(st.session_state["base_url"])

def main():
    st.set_page_config(page_title="MCP Travel Agent", page_icon=":llama:",
                       initial_sidebar_state="collapsed")
    init_session_state()

    with st.sidebar:
        st.subheader("Ollama Settings")
        model_names = [model["display_name"] for model in st.session_state["models"]]
        st.selectbox("Model", options=model_names, key="model_name")
        st.write(f"Base URL: {st.session_state['base_url']}")
        st.radio("Stream Mode", options=["values", "messages"], key="stream_mode")
        st.text_area("System Prompt", key="system_prompt", height=300)
        st.text_area("MCP JSON", key="mcp_json", height=300)

    title_row = st.container(
        horizontal=True,
        vertical_alignment="bottom"
    )

    with title_row:
        st.title("🦙 MCP Travel Agent")
        st.markdown(
            "Use the chat input to send text and images to the agent. You can also use voice input to send a voice message.")
        if len(st.session_state["messages"]) > 0:
            st.button("Clear", icon=":material/refresh:", on_click=new_chat)

    st.divider()

    for message in st.session_state["messages"]:
        display_message(message)

    model = get_selected_model()

    if model is not None:
        accepted_file_types = ["jpg", "jpeg", "png", "gif", "webp"] if model["vision"] else []
        # React to user input
        user_input = multimodal_chat_input(
            placeholder=f"Ask {model['name']} a question...",
            enable_voice_input=True,
            voice_language="en-US",
            voice_recognition_method="web_speech",
            accepted_file_types=accepted_file_types
        )

    if user_input:
        user_message = {"role": "user", "content": user_input}
        display_message(user_message)
        st.session_state["messages"].append(user_message)
        with st.chat_message("assistant"):
            agent = get_agent(
                model,
                st.session_state["base_url"],
                st.session_state["system_prompt"],
                st.session_state["mcp_json"]
            )
            response = st.write_stream(
                agent_chat(agent, user_input, st.session_state["stream_mode"])
            )
        st.session_state["messages"].append({"role": "assistant", "content": response})
        st.rerun()

if __name__ == "__main__":
    main()
