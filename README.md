<div align="center">

<img src="public/streamlit.svg" height="270px"/>

# Ask Chatbot

Streamlit web app providing a Large Language Model (LLM) chatbot with a custom knowledge base

<img src="public/made-with-python.svg" height="30"/>
<img src="public/makes-people-smile.svg" height="30"/>
<img src="public/gen-AI-compatible.svg" height="30"/>

</div>

## [Live Demo](https://ask-chatbot.streamlit.app/)

- Deployed to Streamlit Community Cloud ☁️
- Conversation LLM chatbot chain only
- For ease of use and privacy, the semantic search of personal or organizational documents to create a custom knowledge base for the LLM will be available only as a local deployment feature

## Project Details

- Developed with Python version 3.10
- Streamlit
- LangChain
- OpenAI
- ChromaDB

## Getting Started

- Create a .streamlit folder in the 'src' directory and include the contents of the [.streamlit.example](src/.streamlit.example)

- To initialize a virtual enviroment, navigate to the 'src' directory in the terminal and execute

  ```
  $ python -m venv venv
  ```

- Activate the virtual environment, on MacOS or Linux with

  ```
  $ source venv/bin/activate
  ```

- Install dependencies

  ```
  $ pip install -r requirements.txt
  ```

- Run the app

  ```
  $ streamlit run app.py
  ```

  Open your browser at http://localhost:8501

- To deactivate the virtual environment

  ```
  $ deactivate
  ```

<div align="center">

|                    LLM Conversation                     |
| :-----------------------------------------------------: |
| <img src="./public/ask-chatbot-convo-demo.png" width="950"/> |

</div>