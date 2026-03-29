# Streamlit Recipes

## A project for experimenting with Streamlit and AI agents

This project was developed with Python 3.13 using uv to manage dependencies and the virtual environment.

https://github.com/rscarberry-wa/streamlit_recipes

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

### Ollama Agent Chat

This application introduces an actual agent that uses web search to give up to date answers to questions. It also remembers the thread of conversation, so you can have an ongoing chat.
So this application performs actual chat (it has memory) and it's an agent, since it has a tool that it can use autonomously.

To run:

1. Again, you must have Ollama installed and running with some local models downloaded.
2. Install the `langchain-tavily` library.
3. Set up a Tavily account, obtain an API key, and place the key in your .env file.

Example .env file:
```
OLLAMA_MODEL="gpt-oss:20b"
OLLAMA_BASE_URL="http://localhost:11434/"
TAVILY_API_KEY="<YOUR_API_KEY>"
```

## License

This project is licensed under the Apache License V 2.0.
