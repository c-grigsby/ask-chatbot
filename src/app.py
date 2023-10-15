# @packages
import streamlit as st
from dataclasses import dataclass
from langchain import OpenAI
from langchain.callbacks import get_openai_callback
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationSummaryMemory
from typing import Literal

# Set page configuration
st.set_page_config(page_title="Ask Chatbot")


# Create a data class to contain a message and the sender
@dataclass
class Message:
  """Class for keeping track of a chat messages"""
  origin: Literal["human", "AI"]
  message: str
    
# load_css: Gets CSS styles
def load_css():
  with open("static/styles.css", "r") as f:
    css = f"<style>{f.read()}</style>"
    st.markdown(css, unsafe_allow_html=True)


# initialize_session_state: Creates session state for convo with the LLM
def initialize_session_state():
    # Define chat history in state if not present
    if "history" not in st.session_state:
        st.session_state.history = []
    
    # Define token count in state if not present  
    if "token_count" not in st.session_state:
          st.session_state.token_count = 0
    
    # Define conversation in state if not present
    if "conversation" not in st.session_state:
      # Large Lanuage Model (LLM) for the chatbot
      llm = OpenAI(
        temperature=0,
        openai_api_key=st.secrets["OPENAI_API_KEY"],
        model_name="gpt-3.5-turbo-16k"
      )
      # Create a conversation chain
      st.session_state.conversation = ConversationChain(
        llm=llm,
        memory=ConversationSummaryMemory(llm=llm),
      )
        

# on_click_callback: Manages chat history in session state
def on_click_callback():
  # Wrap code into a get OpenAI callback for the token count
  with get_openai_callback() as callback:
    # Get the prompt from session state
    human_prompt = st.session_state.human_prompt
    
    # Call the conversation chain defined in session state on user prompt
    llm_response = st.session_state.conversation.run(human_prompt)
    
    # Persist the prompt and llm_response in session state
    st.session_state.history.append(Message("human", human_prompt))
    st.session_state.history.append(Message("AI", llm_response))
    
    # Pesist token count in session state
    st.session_state.token_count += callback.total_tokens
    
    # Clear the prompt value
    st.session_state.human_prompt = ""


def main():
  # Load CSS
  load_css()
  
  # Initialize session state
  initialize_session_state()
  
  # Setup the web page 
  st.title("Ask Chatbot 🤖")
  st.header("Let's Talk About Your Data (or Whatever) 💬")


  # Create a placeholder for the chat between the LLM & user
  chat_placeholder = st.container()
  # Create a form for the user prompt
  prompt_placeholder = st.form("chat-form")
  # Create a placeholder for the token count
  token_placeholder = st.empty()


  # Display chat history within chat_placehoder
  with chat_placeholder:
    for chat in st.session_state.history:
      div = f"""
        <div class="chat-row {'' if chat.origin == 'AI' else 'row-reverse'}">
          <img class="chat-icon" src="app/static/{'ai_icon.png' if chat.origin == 'AI' else 'user_icon.png'}" width=32 height=32>
          <div class="chat-bubble {'ai-bubble' if chat.origin == 'AI' else 'human-bubble'}">&#8203;{chat.message}</div>
        </div>
        """
      st.markdown(div, unsafe_allow_html=True)
    
    for _ in range(3):
      st.markdown("")
    
    
  # Create the user prompt within prompt_placeholder
  with prompt_placeholder:
    st.markdown("**Chat**")
    cols = st.columns((6, 1))
    cols[0].text_input(
      "Chat",
      placeholder="Send a message",
      label_visibility="collapsed",
      key="human_prompt",
    )
    cols[1].form_submit_button(
      "Submit", 
      type="primary", 
      on_click=on_click_callback, 
    )

  
  # Display the number of tokens used & conversation context within token_placeholder
  token_placeholder.caption(f"""
  Used {st.session_state.token_count} tokens \n
  Debug LangChain conversation: 
  {st.session_state.conversation.memory.buffer}
  """)

if __name__ == '__main__':
    main()
    