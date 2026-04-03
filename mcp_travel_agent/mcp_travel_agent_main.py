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

@st.dialog("MCP Agent Help")
def show_help_dialog():
    st.markdown("""
            This AI Agent chatbot is preconfigured to find flights for you using an MCP server
            provided by kiwi.com. Since the flight API often returns prices in Euros, an 
            exchange rate server is also hooked in, but you must start it up yourself before
            running this streamlit application.
            
            Even though this is called "MCP Travel Agent", it can be used with any MCP
            servers you wish. You simply have to provide valid MCP configuration JSON
            in the "MCP Configuration" text area.
            
            If you do change the MCP configuration, be sure to also update the system
            prompt appropriately. You wouldn't want to connect the chatbot to an MCP server
            for cooking recipes while telling it to act as a travel agent!
        """)

def main():
    st.set_page_config(page_title="MCP Travel Agent", page_icon="🛫",
                       initial_sidebar_state="collapsed")

    init_session_state()

    with st.sidebar:
        st.subheader("Settings")
        model_names = [model["display_name"] for model in st.session_state["models"]]
        st.selectbox("Model", options=model_names, key="model_name")
        st.write(f"Base URL: {st.session_state['base_url']}")
        st.text_area("System Prompt", key="system_prompt", height=300)
        st.text_area("MCP Configuration", key="mcp_json", height=300)

    title_row = st.container(
        horizontal=True,
        vertical_alignment="bottom"
    )

    with title_row:
        st.title("🛫 MCP Travel Agent")
        st.markdown(
            "Use the chat input to send text and images to the agent. You can also use voice input to send a voice message.")
        st.button(
            "&nbsp;:small[:gray[:material/help: Help]]",
            type="tertiary",
            on_click=show_help_dialog,
        )
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
