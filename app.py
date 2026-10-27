# @packages
from dataclasses import dataclass
from html import escape
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from typing import Literal
import re
import streamlit as st


# OpenAI model used by the chatbot
MODEL_NAME = "gpt-6-luna"

# Chat icons
AI_ICON_URL = "https://ask-chatbot.netlify.app/public/ai_icon.png"
USER_ICON_URL = "https://ask-chatbot.netlify.app/public/user_icon.png"


# Set page configuration
st.set_page_config(page_title="Ask Chatbot")


@dataclass
class Message:
  """
  Class to contain & track messages
  """
  origin: Literal["human", "AI"]
  message: str


def render_code_block(_renderer, tokens, idx, _options, _env):
  """
  Renders a markdown code block as syntax highlighted HTML

  A <div> is used instead of <pre>, as Streamlit takes over the rendering of
  <pre> & drops the highlighting of its children

  Parameters
  ----------
  _renderer : RendererHTML
    The markdown renderer, required by the renderer but unused
  tokens : list of Token
    The tokens of the markdown text
  idx : int
    The index of the code block token
  _options : dict
    The renderer options, required by the renderer but unused
  _env : dict
    The renderer environment, required by the renderer but unused

  Returns
  -------
  str
    The HTML of the code block, plain code when the language is unknown
  """
  token = tokens[idx]
  language = token.info.split()[0] if token.info.strip() else ""
  try:
    code = highlight(token.content, get_lexer_by_name(language), HtmlFormatter(nowrap=True))
  except ClassNotFound:
    code = escape(token.content)
  return f'<div class="code-block">{code.rstrip()}</div>'


# Markdown renderer for LLM responses, raw HTML in a response is escaped
markdown_renderer = MarkdownIt("gfm-like", {"html": False})
markdown_renderer.add_render_rule("fence", render_code_block)
markdown_renderer.add_render_rule("code_block", render_code_block)


def markdown_to_html(text):
  """
  Converts markdown to HTML on a single line, as Streamlit ends an HTML block
  at a blank line & would not render the rest of the message

  Parameters
  ----------
  text : str
    The markdown text

  Returns
  -------
  str
    The HTML, with links opening in a new tab
  """
  html = markdown_renderer.render(text)
  # Open links in a new tab
  html = html.replace("<a href=", '<a target="_blank" rel="noopener noreferrer" href=')
  # Keep the line breaks of code blocks, replace them everywhere else
  parts = re.split(r'(<div class="code-block">.*?</div>)', html, flags=re.DOTALL)
  return "".join(
    part.replace("\n", "&#10;") if part.startswith('<div class="code-block">')
    else part.replace("\n", " ")
    for part in parts
  )


def get_reasoning_summary(llm_response):
  """
  Gets the reasoning summary of an LLM response

  Parameters
  ----------
  llm_response : AIMessage
    The response of the LLM

  Returns
  -------
  str
    The reasoning summary, empty if the model did not reason
  """
  return "  \n".join(
    block.get("reasoning", "")
    for block in llm_response.content_blocks
    if block["type"] == "reasoning"
  )


def chat_row_html(origin, content, bubble_class=""):
  """
  Builds the HTML of a chat row, an icon next to a message bubble

  Parameters
  ----------
  origin : {"human", "AI"}
    Who the message is from
  content : str
    The HTML of the message bubble
  bubble_class : str, optional
    Extra CSS classes for the message bubble

  Returns
  -------
  str
    The HTML of the chat row
  """
  is_ai = origin == "AI"
  return f"""
    <div class="chat-row {'' if is_ai else 'row-reverse'}">
      <img class="chat-icon" src="{AI_ICON_URL if is_ai else USER_ICON_URL}" width=32 height=32>
      <div class="chat-bubble {'ai-bubble' if is_ai else 'human-bubble'} {bubble_class}">{content}</div>
    </div>
    """


def load_css():
  """
  Gets page styles
  """
  with open("./static/styles.css", "r") as f:
    css = f"<style>{f.read()}</style>"
    st.markdown(css, unsafe_allow_html=True)


def initialize_session_state():
  """
  Creates session state for convo with the LLM
  """
  # Define chat history
  if "history" not in st.session_state:
    st.session_state.history = []

  # Define a token count
  if "token_count" not in st.session_state:
    st.session_state.token_count = 0

  # Define the user prompt waiting on an LLM response
  if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

  # Define the error of the latest LLM request
  if "error" not in st.session_state:
    st.session_state.error = None

  # Define the reasoning summary of the latest LLM response
  if "reasoning" not in st.session_state:
    st.session_state.reasoning = ""

  # Define the LLM messages sent as conversation context
  if "messages" not in st.session_state:
    st.session_state.messages = []

  # Define the Large Language Model (LLM) for the chatbot
  if "llm" not in st.session_state:
    st.session_state.llm = ChatOpenAI(
      api_key=st.secrets["OPENAI_API_KEY"],
      model=MODEL_NAME,
      # The Responses API returns a summary of the model's reasoning
      use_responses_api=True,
      reasoning={"effort": "medium", "summary": "auto"}
    )


def on_click_callback():
  """
  Shows the user prompt right away & queues it for the LLM
  """
  # Get the prompt from session state
  human_prompt = st.session_state.human_prompt.strip()
  if not human_prompt:
    return

  # Persist the prompt in session state & mark it as waiting on the LLM
  st.session_state.history.append(Message("human", human_prompt))
  st.session_state.pending_prompt = human_prompt
  st.session_state.error = None

  # Clear the prompt value
  st.session_state.human_prompt = ""


def answer_pending_prompt():
  """
  Calls the LLM on the pending prompt & manages the response in session state
  """
  human_prompt = st.session_state.pending_prompt
  st.session_state.pending_prompt = None

  # Call the LLM with the conversation so far plus the user prompt
  messages = st.session_state.messages + [HumanMessage(human_prompt)]
  try:
    llm_response = st.session_state.llm.invoke(messages)
  except Exception as error:
    st.session_state.error = f"The model could not respond: {error}"
    return
  st.session_state.messages = messages + [AIMessage(llm_response.text)]

  # Persist the llm_response in session state
  st.session_state.history.append(Message("AI", llm_response.text))

  # Persist the reasoning summary of the response in session state
  st.session_state.reasoning = get_reasoning_summary(llm_response)

  # Persist token count in session state
  st.session_state.token_count += llm_response.usage_metadata["total_tokens"]


def main():

  load_css()
  initialize_session_state()

  # Setup web page text
  st.title("Ask Chatbot 🤖")
  st.header("Let's Talk About Your Data (or Whatever) 💬")

  # Create a container for the chat between the user & LLM
  chat_placeholder = st.container()
  # Create a form for the user prompt
  prompt_placeholder = st.form("chat-form")
  # Create a empty placeholder for the token count
  token_placeholder = st.empty()


  # Display chat history within chat_placehoder
  with chat_placeholder:
    for chat in st.session_state.history:
      # The LLM replies in markdown, user prompts are shown as plain text
      content = (
        markdown_to_html(chat.message) if chat.origin == "AI" else escape(chat.message)
      )
      st.markdown(chat_row_html(chat.origin, content), unsafe_allow_html=True)

    # Display a typing bubble while waiting on the LLM response
    if st.session_state.pending_prompt:
      st.markdown(
        chat_row_html("AI", "<span></span><span></span><span></span>", "typing-bubble"),
        unsafe_allow_html=True
      )

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


  # Display the error of the latest LLM request
  if st.session_state.error:
    st.error(st.session_state.error)

  # Display # of tokens used & the reasoning summary within token_placeholder
  token_placeholder.caption(f"""
  Used {st.session_state.token_count} tokens \n
  Model reasoning summary ({MODEL_NAME}): \n
  {st.session_state.reasoning or "No reasoning summary for this response."}
  """)

  # Answer the prompt last, so the page above is already rendered while waiting
  if st.session_state.pending_prompt:
    answer_pending_prompt()
    st.rerun()


if __name__ == '__main__':
  main()
