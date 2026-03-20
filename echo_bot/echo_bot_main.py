import streamlit as st
import random
import time

def response_generator():
    response = random.choice(
        [
            "Hello there! How can I assist you today?",
            "Hi, human! Is there anything I can help you with?",
            "Do you need help?",
        ]
    )
    for word in response.split():
        yield word + " "
        time.sleep(0.1)

def clear_messages():
    st.session_state["messages"] = []

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

title_row = st.container(
    horizontal=True,
    vertical_alignment="bottom"
)

with title_row:
    st.title("Echo Bot")
    if len(st.session_state["messages"]) > 0:
        st.button("Clear", on_click=clear_messages)

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
        response = st.write_stream(response_generator())
    st.session_state["messages"].append({"role": "assistant", "content": response})

