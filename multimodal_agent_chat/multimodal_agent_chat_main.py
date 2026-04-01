from typing import Dict, Any

import streamlit as st
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langchain_tavily import TavilySearch
import ollama
import os
import base64
from st_chat_input_multimodal import multimodal_chat_input

# First streamlit op in the application
st.set_page_config(page_title="Ollama Multimodal Agent Chat", page_icon=":llama:", initial_sidebar_state="collapsed")

def init_session_state():
    """Initialize session state with default values. This should be called prior to accessing any session state variables."""
    default_state = {
        "messages": [],
        "model_name": None,
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

@st.cache_resource(show_spinner="Loading model...")
def get_agent(model: Dict[str, Any], base_url: str, system_prompt: str):
    llm = ChatOllama(model=model["name"], base_url=base_url)
    tools = [TavilySearch()] if model["tools"] else []
    agent = create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=InMemorySaver(),
    )
    return agent

@st.cache_data
def get_models(base_url: str):
    client = ollama.Client(host=base_url)
    model_list = client.list()
    models = []
    for m in model_list["models"]:
        info = ollama.show(m.model)
        capabilities = info["capabilities"]
        if "tools" in capabilities or "vision" in capabilities:
            display_name = m.model
            if "vision" in capabilities:
                display_name += " 🔎"
            if "tools" in capabilities:
                display_name += " 🛠️"
            models.append({
                "name": m.model,
                "display_name": display_name,
                "vision": "vision" in capabilities,
                "tools": "tools" in capabilities,
            })
    return models

def get_selected_model() -> Dict[str, Any] | None:
    """Get the dictionary describing the selected model."""
    display_name = st.session_state["model_name"]
    if display_name is None:
        return None
    for model in st.session_state["models"]:
        if model["display_name"] == display_name:
            return model
    return None

def new_chat():
    st.session_state["messages"] = []
    st.session_state["thread_id"] += 1

def mime_type_from_file_name(file_name):
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    extension = os.path.splitext(file_name)[1].lower()
    return mime_types.get(extension, None)

def agent_chat(agent, user_input, stream_mode: str = "values"):
    content = []
    if user_input.get("text"):
        content.append({"type": "text", "text": user_input["text"]})
    if user_input.get("files"):
        for file in user_input["files"]:
            mime_type = mime_type_from_file_name(file['name'])
            if mime_type is not None:
                base64_data = file['data'].split(',')[1] if ',' in file['data'] else file['data']
                content.append({"type": "image", "base64": base64_data, "mime_type": mime_type})

    human_message = HumanMessage(content=content)

    if stream_mode == "values":
        for step in agent.stream(
                {"messages": [human_message]},
                {"configurable": {"thread_id": str(st.session_state["thread_id"])}},
                stream_mode="values"
        ):
            last_message = step["messages"][-1]
            if isinstance(last_message, AIMessage):
                yield last_message.content
    else:  # messages
        for token, metadata in agent.stream(
                {"messages": [human_message]},
                {"configurable": {"thread_id": str(st.session_state["thread_id"])}},
                stream_mode="messages"
        ):
            yield token.content

# Load required environment vars (API keys, etc.)
load_dotenv()
# Initialize the session state
init_session_state()

if "models" not in st.session_state:
    st.session_state["models"] = get_models(st.session_state["base_url"])

title_row = st.container(
    horizontal=True,
    vertical_alignment="bottom"
)

with st.sidebar:
    st.subheader("Ollama Settings")
    model_names = [model["display_name"] for model in st.session_state["models"]]
    model = st.selectbox("Model", options=model_names, key="model_name")
    st.write(f"Base URL: {st.session_state['base_url']}")
    st.radio("Stream Mode", options=["values", "messages"], key="stream_mode")
    st.text_area("System Prompt", key="system_prompt", height=300)

with title_row:
    st.title("🦙 Multimodal Ollama Agent Chat")
    st.markdown("Use the chat input to send text and images to the agent. You can also use voice input to send a voice message.")
    if len(st.session_state["messages"]) > 0:
        st.button("Clear", icon=":material/refresh:", on_click=new_chat)

st.divider()

# Display history messages
for message in st.session_state["messages"]:
    if message["role"] == "user":
        with st.chat_message("user"):  # Must be "user" or "assistant"
           user_input = message["content"]
           if "text" in user_input:
               st.write(user_input["text"])
           if "files" in user_input:
                for file in user_input["files"]:
                    try:
                        base64_data = file['data'].split(',')[1] if ',' in file['data'] else file['data']
                        image_bytes = base64.b64decode(base64_data)
                        st.image(image_bytes, caption=file['name'], width=200)
                    except Exception as e:
                        st.error(f"Error processing file {file['name']}: {e}")
    elif message["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(message["content"])

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
        with st.chat_message("user"):
            if "text" in user_input:
                st.write(user_input["text"])
            if "files" in user_input:
                for file in user_input["files"]:
                    try:
                        base64_data = file['data'].split(',')[1] if ',' in file['data'] else file['data']
                        image_bytes = base64.b64decode(base64_data)
                        st.image(image_bytes, caption=file['name'], width=200)
                    except Exception as e:
                        st.error(f"Error processing file {file['name']}: {e}")
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("assistant"):
            agent = get_agent(
                model,
                st.session_state["base_url"],
                st.session_state["system_prompt"]
            )
            response = st.write_stream(
                agent_chat(agent, user_input, st.session_state["stream_mode"])
            )
        st.session_state["messages"].append({"role": "assistant", "content": response})
        st.rerun()