import asyncio
import json
import queue
import threading
from typing import Dict, Any

import ollama
import streamlit as st
import os

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
import base64

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import InMemorySaver
from mcp_utils import McpRetryInterceptor


@st.cache_data
def get_models(
        base_url: str,
        must_support_tools: bool = True,
        must_support_vision: bool = False) -> list[Dict[str, Any]]:
    """Get the list of available models."""
    client = ollama.Client(host=base_url)
    model_list = client.list()
    models = []
    for m in model_list["models"]:
        info = ollama.show(m.model)
        capabilities = info["capabilities"]
        tool_ok = "tools" in capabilities if must_support_tools else True
        vision_ok = "vision" in capabilities if must_support_vision else True
        if tool_ok or vision_ok:
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

async def get_mcp_tools(mcp_json: str):
    mcp_config = None
    if mcp_json:
        try:
            mcp_config = json.loads(mcp_json)
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse MCP JSON: {e}")
            return None
    if mcp_config:
        try:
            # The McpRetryInterceptor will retry failed requests
            client = MultiServerMCPClient(mcp_config, tool_interceptors=[McpRetryInterceptor()])
            tools = await client.get_tools()
            return tools
        except Exception as e:
            st.error(f"Failed to get tools from MCP: {e}")
            return None

@st.cache_resource(show_spinner="Loading model...")
def get_agent(model: Dict[str, Any], base_url: str, system_prompt: str, mcp_json: str):
    llm = ChatOllama(model=model["name"], base_url=base_url)
    tools = asyncio.run(get_mcp_tools(mcp_json))
    agent = create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=InMemorySaver(),
    )
    return agent

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

# Persistent event loop running in a background thread.
# Using asyncio.run() per call closes the loop each time, which breaks the
# httpx connection pool inside the cached ChatOllama client on subsequent calls.
_bg_loop: asyncio.AbstractEventLoop | None = None
_bg_loop_thread: threading.Thread | None = None


def _get_bg_loop() -> asyncio.AbstractEventLoop:
    global _bg_loop, _bg_loop_thread
    if _bg_loop is None or not _bg_loop.is_running():
        _bg_loop = asyncio.new_event_loop()
        _bg_loop_thread = threading.Thread(target=_bg_loop.run_forever, daemon=True)
        _bg_loop_thread.start()
    return _bg_loop


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
    thread_config = {"configurable": {"thread_id": str(st.session_state["thread_id"])}}

    # MCP tools are async-only, so we must use astream(). Submit the coroutine
    # to a persistent background event loop so the httpx connection pool inside
    # the cached ChatOllama is never bound to a closed loop across calls.
    _SENTINEL = object()
    chunk_queue: queue.Queue = queue.Queue()

    async def _run_async():
        try:
            if stream_mode == "values":
                async for step in agent.astream(
                        {"messages": [human_message]},
                        thread_config,
                        stream_mode="values"
                ):
                    last_message = step["messages"][-1]
                    if isinstance(last_message, AIMessage):
                        chunk_queue.put(last_message.content)
            else:  # messages
                async for token, metadata in agent.astream(
                        {"messages": [human_message]},
                        thread_config,
                        stream_mode="messages"
                ):
                    chunk_queue.put(token.content)
        except Exception as e:
            chunk_queue.put(e)
        finally:
            chunk_queue.put(_SENTINEL)

    asyncio.run_coroutine_threadsafe(_run_async(), _get_bg_loop())

    while True:
        item = chunk_queue.get()
        if item is _SENTINEL:
            break
        if isinstance(item, Exception):
            raise item
        yield item

def display_message(message):
    """Display a message in the chat window."""
    if message["role"] == "user":
        # For user messages, display the text and images separately
        with st.chat_message("user"):
           user_input = message["content"]
           if "text" in user_input:
               st.write(user_input["text"])
           if "files" in user_input:
                for file in user_input["files"]:
                    try:
                        base64_data = file['data'].split(',')[1] if ',' in file['data'] else file['data']
                        image_bytes = base64.b64decode(base64_data)
                        st.image(image_bytes, caption=file['name'], width=600)
                    except Exception as e:
                        st.error(f"Error processing file {file['name']}: {e}")
    elif message["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(message["content"])

