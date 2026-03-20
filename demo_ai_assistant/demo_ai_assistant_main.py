import streamlit as st
import datetime
from htbuilder.units import rem
from htbuilder import div, styles

st.set_page_config(page_title="Demo AI Assistant", page_icon="✨")

# Can find the material shortcodes at https://fonts.google.com/icons?icon.size=24&icon.color=%23e3e3e3
# Just lowercase and replace spaces with underscores.
SUGGESTIONS = {
    ":blue[:material/local_library:] What is Streamlit?": (
        "What is Streamlit, what is it great at, and what can I do with it?"
    ),
    ":green[:material/database:] Help me understand session state": (
        "Help me understand session state. What is it for? "
        "What are gotchas? What are alternatives?"
    ),
    ":orange[:material/multiline_chart:] How do I make an interactive chart?": (
        "How do I make a chart where, when I click, another chart updates? "
        "Show me examples with Altair or Plotly."
    ),
    ":violet[:material/apparel:] How do I customize my app?": (
        "How do I customize my app? What does Streamlit offer? No hacks please."
    ),
    ":red[:material/deployed_code:] Deploying an app at work": (
        "How do I deploy an app at work? Give me easy and performant options."
    ),
}

def show_feedback_controls(message_index):
    """Shows the "How did I do?" control"""
    st.write("")
    with st.popover("How did I do?"):
        with st.form(key=f"feedback_{message_index}", border=False):
            with st.container(gap=None):
                st.markdown(":small[Rating]")
                rating = st.feedback(options="stars")

            details = st.text_area("More information (optional)")

            if st.checkbox("Include chat history with my feedback", True):
                relevant_history = st.session_state["messages"][:message_index]
            else:
                relevant_history = []

            "" # Add some space
            if st.form_submit_button("Send feedback"):
                pass

@st.dialog("Legal disclaimer")
def show_disclaimer_dialog():
    st.caption("""
            This AI chatbot is powered by Snowflake and public Streamlit
            information. Answers may be inaccurate, inefficient, or biased.
            Any use or decisions based on such answers should include reasonable
            practices including human oversight to ensure they are safe,
            accurate, and suitable for your intended purpose. Streamlit is not
            liable for any actions, losses, or damages resulting from the use
            of the chatbot. Do not enter any private, sensitive, personal, or
            regulated data. By using this chatbot, you acknowledge and agree
            that input you provide and answers you receive (collectively,
            “Content”) may be used by Snowflake to provide, maintain, develop,
            and improve their respective offerings. For more
            information on how Snowflake may use your Content, see
            https://streamlit.io/terms-of-service.
        """)

# Displays the graphic symbol using the styles
st.html(div(style=styles(font_size=rem(5), line_height=1))["❉"])

title_row = st.container(
    horizontal=True,
    vertical_alignment="bottom",
    border=True
)

with title_row:
    # ":material/cognition_2: Streamlit AI assistant", anchor=False, width="stretch"
    st.title("Demo AI Assistant", anchor=False, width="stretch")

user_just_asked_initial_question = (
    "initial_question" in st.session_state and st.session_state["initial_question"]
)

user_just_clicked_suggestion = (
    "selected_suggestion" in st.session_state and st.session_state["selected_suggestion"]
)

user_first_interaction = (
    user_just_asked_initial_question or user_just_clicked_suggestion
)

has_message_history = (
    "messages" in st.session_state and len(st.session_state["messages"]) > 0
)

# Show a different UI if the user hasn't asked a question yet.
if not user_first_interaction and not has_message_history:
    st.session_state["messages"] = []

    with st.container():
        st.chat_input("Ask a question...", key="initial_question")
        selected_suggestion = st.pills(
            label="Examples",
            label_visibility="collapsed",
            options=SUGGESTIONS.keys(),
            key="selected_suggestion"
        )

    st.button(
        "&nbsp;:small[:gray[:material/balance: Legal disclaimer]]",
        type="tertiary",
        on_click=show_disclaimer_dialog,
    )

    # Keeps the script from running anything below this line
    st.stop()

# Show chat input at the bottom when a question has been asked
user_message = st.chat_input("Ask a follow-up...")

if not user_message:
    if user_just_asked_initial_question:
        user_message = st.session_state["initial_question"]
    if user_just_clicked_suggestion:
        user_message = SUGGESTIONS[st.session_state["selected_suggestion"]]

with title_row:
    def clear_conversation():
        st.session_state["messages"] = []
        st.session_state["initial_question"] = None
        st.session_state["selected_suggestion"] = None
    # Will appear to the right of the title.
    st.button("Restart", icon=":material/refresh:", on_click=clear_conversation)

if "prev_question_timestamp" not in st.session_state:
    st.session_state["prev_question_timestamp"] = datetime.datetime.fromtimestamp(0)

# Display chat messages from history as speech bubbles
for i, message in enumerate(st.session_state["messages"]):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.container() # Fix ghost message bug
        st.markdown(message["content"])
        if message["role"] == "assistant":
            show_feedback_controls(i)

if user_message:
    # So streamlit's markdown engine doesn't interpret it as LaTeX code.
    user_message = user_message.replace("$", r"\$")

    # Display message as a speech bubble
    with st.chat_message("user"):
        st.text(user_message)