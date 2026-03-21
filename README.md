# Streamlit Recipes

## A project for experimenting with Streamlit and AI agents

This project was developed with Python 3.13 using uv to manage dependencies and the virtual environment.

### Simple Ollama Query

A simple Streamlit app for querying various Ollama models that have been downloaded to the server. Since no chat history is maintained, every query is independent of the previous ones.

To run:

1. Install Ollama and start the server either locally or on an accessible remote server.
2. Create an .env with contents similar to the following, but with a model you've downloaded to the server and the correct base URL:
```  
OLLAMA_MODEL="gemma3:27b"
OLLAMA_BASE_URL="http://localhost:11434/"
```
3. Install the dependent libraries `streamlit, langchain, langchain-ollama, dotenv`
4. Run `streamlit run simple_ollama_chat/simple_ollama_chat_main.py`
5. Select a model and start chatting.

## License

This project is licensed under the Apache License V 2.0.
