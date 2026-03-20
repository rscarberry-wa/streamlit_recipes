import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
import ollama
import os

st.set_page_config(page_title="Ollama Chat", page_icon=":llama:", initial_sidebar_state="collapsed")

if "model_name" not in st.session_state:
    # Load environment variables from .env file
    load_dotenv()
    st.session_state["model_name"] = os.getenv("OLLAMA_MODEL", "gemma3:27b")
    st.session_state["base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/")
if "about_models" not in st.session_state:
    st.session_state["about_models"] = {}

# To reduce the display size of the Parameters and Quantization metrics
st.markdown("""
<style>
[data-testid="stMetricValue"] {
    font-size: 20px;
}
[data-testid="stMetricLabel"] {
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def get_about_model(model_name, _llm):
    try:
        return _llm.invoke({"user_input": "Tell me about yourself"}).content
    except Exception:
        return f"{model_name} does not support chat."

@st.cache_resource(show_spinner="Loading model...")
def get_model(model_name: str, base_url: str):
    llm = ChatOllama(model=model_name, base_url=base_url)
    prompt = PromptTemplate(
        input_variables=["user_input"],
        template="Respond to the user input: {user_input}"
    )
    llm = prompt | llm
    return llm

@st.cache_data
def get_models(base_url: str):
    client = ollama.Client(host=base_url)
    return client.list()

def clear_messages():
    st.session_state["messages"] = []

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

llm = get_model(st.session_state["model_name"], st.session_state["base_url"])

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

    if "model_name" in st.session_state and st.session_state["model_name"]:
        model_name = st.session_state["model_name"]
        model = None
        for m in st.session_state["models"]["models"]:
            if m.model == model_name:
                model = m
                break
        if model is not None:
            st.divider()

            details = model.details
            # Parameter size and quantization
            col1, col2 = st.sidebar.columns(2)
            with col1:
                st.metric("Parameters",details.get('parameter_size', 'N/A'))
            with col2:
                st.metric("Quantization", details.get('quantization_level', 'N/A'))

            # Family and format
            st.sidebar.write(f"**Family:** {details.get('family', 'N/A')}")
            st.sidebar.write(f"**Format:** {details.get('format', 'N/A')}")

            # Size information
            size_gb = model.get('size', 0) / (1024 ** 3)
            st.sidebar.write(f"**Size:** {size_gb:.2f} GB")

            # Last modified
            modified_at = model.get('modified_at')
            if modified_at:
                if isinstance(modified_at, datetime):
                    modified_str = modified_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    modified_str = str(modified_at)
                st.sidebar.write(f"**Modified:** {modified_str}")

            # Digest (truncated)
            digest = model.get('digest', '')
            if digest:
                st.sidebar.write(f"**Digest:** `{digest[:16]}...`")

        # Display "About {model_name}" text area
        if model_name not in st.session_state["about_models"]:
            st.write("")
            st.session_state["about_models"][model_name] = get_about_model(model_name, llm)
            st.rerun()
        else:
            st.divider()
            st.markdown(f"### About {model_name}")
            st.write(st.session_state["about_models"][model_name])

with title_row:
    st.title("🦙 Chat with Ollama Models")
    if len(st.session_state["messages"]) > 0:
        st.button("Clear", icon=":material/refresh:",on_click=clear_messages)

st.divider()

# Display history messages
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]): # Must be "user" or "assistant"
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What's up?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        llm = get_model(st.session_state["model_name"], st.session_state["base_url"])
        try:
            response = st.write_stream(
                llm.stream({"user_input": prompt})
            ) + f"\n\n*answered by {st.session_state['model_name']}*"
        except Exception as e:
            response = f"Error: {e}"
    st.session_state["messages"].append({"role": "assistant", "content": response})
    st.rerun()
