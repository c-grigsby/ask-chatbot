# @packages
from dataclasses import dataclass
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback
from langchain.chains.conversation.memory import ConversationSummaryMemory
from langchain.document_loaders import DirectoryLoader
from langchain.document_loaders import Docx2txtLoader
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import TextLoader
from langchain.document_loaders import UnstructuredExcelLoader
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from typing import Literal
import os 
import shutil
import streamlit as st
# @scripts
from helpers.web_scraping import web_scrape_site


# Get the API key for the LLM & embedding model (If required, currently using OpenAI)
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# Set page configuration
st.set_page_config(page_title="Ask Chatbot")


@dataclass
class Message:
  """
  Class to contain & track messages
  """
  origin: Literal["human", "AI"]
  message: str


def load_directory_documents(path_to_data):
  """
  Loads & extracts text data within a local directory for a custom knowledge base. 
  Accepts the path_to_data.
  Anticipates to load any .txt, .pdf, .csv, .docx, or .xlsx files in the directory. 
  Many loader classes available, see docs: https://python.langchain.com/docs/integrations/document_loaders
  Retuns the text documents.
  """
  # Define loaders
  pdf_loader = DirectoryLoader(path_to_data, glob="./*.pdf", loader_cls=PyPDFLoader, use_multithreading=True)
  txt_loader = DirectoryLoader(path_to_data, glob="./*.txt", loader_cls=TextLoader)
  csv_loader = DirectoryLoader(path_to_data, glob="./*.csv", loader_cls=CSVLoader)
  word_loader = DirectoryLoader(path_to_data, glob="./*.docx", loader_cls=Docx2txtLoader)
  excel_loader = DirectoryLoader(path_to_data, glob="./*.xlsx", loader_cls=UnstructuredExcelLoader)
  
  loaders = [pdf_loader, txt_loader, csv_loader, word_loader, excel_loader]
  documents = []
  for loader in loaders:
    documents.extend(loader.load())
  
  if len(documents) == 0: 
    # Terminate the app if no data found
    st.write(f"No data found within: {path_to_data}")
    st.stop()
  
  # Display results
  filenames = []
  filenames.append("Uploaded Documents:")
  for doc in documents:
    filename = doc.metadata.get('source')
    # There will be multiple .csv docs per uploaded .csv
    if filename not in filenames:
      filenames.append(filename)
    
  # Remove text before the last '/' character
  cleaned_filenames = [filename.split('/')[-1] for filename in filenames]
  # Combine the filenames into a single string for the HTML
  filenames_combined = "<br>".join(cleaned_filenames)
  div = f"""
        <div class="chat-row">
          <div class="chat-bubble human-bubble">&#8203;{filenames_combined}</div>
        </div>
        """
  st.markdown(div, unsafe_allow_html=True)
    
  return documents


def get_chunks(documents):
  """
  Chunks the documents for vector embedding.
  Accepts a list of documents & returns the split text.
  """
  # Chunk data for embedding
  text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
  texts = text_splitter.split_documents(documents)
  
  return texts
  

def embed_and_persist_vectors(texts, persist_dir):
  """
  Performs vector embeddings and persists the Chorma vector store to disk.
  Accepts the split texts & a path to store the vectors.
  Returns the persist_directory that was used.
  Note: Different embedding models will output different vector dimensionalities,
  require different resources, and have different performance characteristics.
  Ensure vector compatibility with the LLM chatbot.
  """
  try:
    # Create a Chroma vector store and embed the split text
    vector_store = Chroma.from_documents(
      documents=texts, 
      embedding=OpenAIEmbeddings(),
      persist_directory=persist_dir
      )

    # Persist the vector store to disk
    vector_store.persist()
    vector_store = None
    
  except Exception as e:
    print("An error occurred creating the vector store: ", e)
    
  return persist_dir


def create_vector_store(persist_dir):
  """
  Loads & returns the Chroma vector store persisted on disk. 
  Accepts the path where the vectors were stored & returns the vector store.
  Note: If the knowledge base is unchanged, embedding & persisting the data first can be skipped.
  Useful when embedding large amounts of data.
  """
  # Loads the vector store persisted to disk
  vector_store = Chroma(persist_directory=persist_dir, embedding_function=OpenAIEmbeddings())
  
  return vector_store


def load_and_process_data(path_to_data, persist_dir, remove_existing_persist_dir):
  """
  Executes functions to load & process data, perform vector embedding, and persist results.
  Accepts a path for the data to load, the persist directory, 
  and a boolean to clear the current vector store.
  """
  # Cleans the existing persist directory
  if os.path.exists(persist_dir) and remove_existing_persist_dir:
    try:
      # Delete files & subdirectories within the directory
      absolute_path = os.path.abspath(persist_dir)
      shutil.rmtree(absolute_path)
      print(f"Deleted directory: {absolute_path}")
      
    except Exception as e:
      print(f"Error while deleting directory: {e}")
      
  if not os.path.exists(persist_dir):
    try:  
      os.makedirs(persist_dir)
      
    except Exception as e:
      print(f"Error making directory: {e}")

  # Loads text from the documents
  documents = load_directory_documents(path_to_data)
  print(f"Loaded {len(documents)} documents")
  
  # Splits data for vector embedding
  texts = get_chunks(documents)
  print(f"Split into {len(texts)} chunks")
  
  # Performs vector embedding and persists results
  persist_dir = embed_and_persist_vectors(texts, persist_dir)
  print(f"Persisted vectors to: {persist_dir}")


def load_css():
  """
  Retrieves page styles
  """
  with open("./static/styles.css", "r") as f:
    css = f"<style>{f.read()}</style>"
    st.markdown(css, unsafe_allow_html=True)


def init_web_scraping():
  """
  Executes helper functions for web scrapping the text from a website.
  Default behavior will also search & scrape any links with an 'a' tag on the website.
  """
  demo_website_url = "https://www.upeccu.com/"
  output_folder_name = "data"
  web_scrape_site(demo_website_url, output_folder_name)


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
  
  # Define vars to ensure a block of code is run only once
  if 'web_scraping' not in st.session_state:
    st.session_state.web_scraping = False
    
  if 'load_and_process' not in st.session_state:
    st.session_state.load_and_process = False

  # Define a conversation chain 
  if "conversation" not in st.session_state:
    
    # Path to the data to process 
    path_to_data = "./data/"
    # Name for the local vector store
    db_name = "demo"
    # Directory to persist/load the vector store
    persist_dir = f"chroma-db_{db_name}"
    
    # Web scraping functionality
    web_scraping_actions = True
    if web_scraping_actions and not st.session_state.web_scraping:
      with st.spinner("Web scraping site..."):
        
        # Executes web scraping on the URL defined in the function above
        init_web_scraping()
        st.session_state.web_scraping = True
    
    # Load data functionality
    load_data = True
    remove_existing_persist_dir = True
    if load_data and not st.session_state.load_and_process:
      with st.spinner("Loading data and creating vector embeddings..."):
        
        # Loads data & creates vector embeddings
        load_and_process_data(path_to_data, persist_dir, remove_existing_persist_dir)
        st.session_state.load_and_process = True
    
    # Create a vector store to serve the custom knowledge base
    vector_store = create_vector_store(persist_dir)
      
    # Define the Large Lanuage Model (LLM) for the chatbot
    llm = ChatOpenAI(
      temperature=0,
      model_name="gpt-3.5-turbo"
      )
    
    # Define the conversational retrieval chain
    st.session_state.conversation = ConversationalRetrievalChain.from_llm(
      llm=llm,
      # Define a retriever for the knowledge base context
      retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
      # Create a Memory object 
      memory = ConversationSummaryMemory(llm=llm, memory_key="chat_history", return_messages=True)
      )
      
        
def on_click_callback():
  """
  Manages chat history in session state
  """
  # Wrap code into a get OpenAI callback for the token count
  with get_openai_callback() as callback:
    # Get the prompt from session state
    human_prompt = st.session_state.human_prompt
    
    # Call the conversation chain defined in session state on user prompt
    llm_response = st.session_state.conversation({"question": human_prompt})
    
    # Persist the prompt and llm_response in session state
    st.session_state.history.append(Message("human", human_prompt))
    st.session_state.history.append(Message("AI", llm_response['answer']))
    
    # Pesist token count in session state
    st.session_state.token_count += callback.total_tokens
    
    # Clear the prompt value
    st.session_state.human_prompt = ""


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
      div = f"""
        <div class="chat-row {'' if chat.origin == 'AI' else 'row-reverse'}">
          <img class="chat-icon" src="{'https://ask-chatbot.netlify.app/public/ai_icon.png' if chat.origin == 'AI' else 'https://ask-chatbot.netlify.app/public/user_icon.png'}" width=32 height=32>
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

  # Display # of tokens used & conversation context within token_placeholder
  token_placeholder.caption(
    f"""
    Used {st.session_state.token_count} tokens \n
    Debug LangChain conversation: 
    {st.session_state.conversation.memory.buffer}
    """
    )


if __name__ == '__main__':
  main()
    