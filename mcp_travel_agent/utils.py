import ollama
import streamlit as st
import os
from langchain_core.messages import AIMessage, HumanMessage
import base64

@st.cache_data
def get_models(base_url: str, must_support_tools: bool = True, must_support_vision: bool = False):
    client = ollama.Client(host=base_url)
    model_list = client.list()
    models = []
    for m in model_list["models"]:
        info = ollama.show(m.model)
        capabilities = info["capabilities"]
        tool_ok = "tools" in capabilities if must_support_tools else True
        vision_ok = "vision" in capabilities if must_support_vision else True
        if tool_ok or vision_ok:
            models.append(m.model)
    return models

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
