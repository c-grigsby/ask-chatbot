# @packages
import streamlit as st

# Define and initialize session state
def initialize_session_state():
    if "history" not in st.session_state:
        st.session_state.history = []
        
initialize_session_state()


# on_click_callback: Manages chat history in session state
def on_click_callback():
  human_prompt = st.session_state.human_prompt
  st.session_state.history.append(human_prompt)


# Setup the web page 
st.set_page_config(page_title="Ask Chatbot")
st.title("Ask Chatbot 🤖")
st.header("Let's Talk About Your Data (or Whatever) 💬")


# Add a placeholder for the chat between the LLM & user
chat_placeholder = st.container()
# Create a form for the user prompt
prompt_placeholder = st.form("chat-form")


# Display chat history within the chat_placehoder
with chat_placeholder:
  for chat in st.session_state.history:
    st.markdown(chat)
  
  
# Create the user prompt within the prompt_placeholder
with prompt_placeholder:
    st.markdown("**Chat**")
    cols = st.columns((6, 1))
    cols[0].text_input(
        "Chat",
        value="Hello chatbot",
        label_visibility="collapsed",
        key="human_prompt",
    )
    cols[1].form_submit_button(
        "Submit", 
        type="primary", 
        on_click=on_click_callback, 
    )
    