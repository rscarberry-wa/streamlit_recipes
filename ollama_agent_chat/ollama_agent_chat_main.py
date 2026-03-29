import streamlit as st
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langchain_tavily import TavilySearch
import ollama
import os

st.set_page_config(page_title="Ollama Agent Chat", page_icon=":llama:", initial_sidebar_state="collapsed")

if "model_name" not in st.session_state:
    # Load environment variables from .env file
    load_dotenv()
    st.session_state["model_name"] = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
    st.session_state["base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/")
if "system_prompt" not in st.session_state:
    st.session_state["system_prompt"] = (
        "You are a helpful assistant. Whenever the user asks you questions about "
        "current events, use your web search tools to obtain the most up to date information."
    )
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = 1
if "stream_mode" not in st.session_state:
    st.session_state["stream_mode"] = "values"
    
@st.cache_resource(show_spinner="Loading model...")
def get_agent(model_name: str, base_url: str, system_prompt: str):
    llm = ChatOllama(model=model_name, base_url=base_url)
    agent = create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[TavilySearch()],
        checkpointer=InMemorySaver(),
    )
    return agent

@st.cache_data
def get_models(base_url: str):
    client = ollama.Client(host=base_url)
    return client.list()

def new_chat():
    st.session_state["messages"] = []
    st.session_state["thread_id"] += 1

def agent_chat(agent, prompt: str, stream_mode: str = "values"):
    if stream_mode == "values":
        for step in agent.stream(
                {"messages": [{"role": "user", "content": prompt}]},
                {"configurable": {"thread_id": str(st.session_state["thread_id"])}},
                stream_mode="values"
        ):
            last_message = step["messages"][-1]
            if isinstance(last_message, AIMessage):
                yield last_message.content
    else:  # messages
        for token, metadata in agent.stream(
                {"messages": [{"role": "user", "content": prompt}]},
                {"configurable": {"thread_id": str(st.session_state["thread_id"])}},
                stream_mode="messages"
        ):
            yield token.content

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

agent = get_agent(
    st.session_state["model_name"], 
    st.session_state["base_url"],
    st.session_state["system_prompt"]
)

if "models" not in st.session_state:
    st.session_state["models"] = get_models(st.session_state["base_url"])

title_row = st.container(
    horizontal=True,
    vertical_alignment="bottom"
)

with st.sidebar:
    st.subheader("Ollama Settings")
    model_names = [model.model for model in st.session_state["models"]["models"]]
    model = st.selectbox("Model", options=model_names, key="model_name")
    st.write(f"Base URL: {st.session_state['base_url']}")
    st.radio("Stream Mode", options=["values", "messages"], key="stream_mode")
    st.text_area("System Prompt", key="system_prompt", height=300)

with title_row:
    st.title("🦙 Chat with an Ollama Agent")
    if len(st.session_state["messages"]) > 0:
        st.button("Clear", icon=":material/refresh:",on_click=new_chat)

st.divider()

# Display history messages
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]): # Must be "user" or "assistant"
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input(f"Ask {st.session_state['model_name']} a question:"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        agent = get_agent(
            st.session_state["model_name"],
            st.session_state["base_url"],
            st.session_state["system_prompt"]
        )

        response = st.write_stream(
            agent_chat(agent, prompt, st.session_state["stream_mode"])
        )

        # except Exception as e:
        #     response = f"Error: {e}"
    st.session_state["messages"].append({"role": "assistant", "content": response})
    st.rerun()
