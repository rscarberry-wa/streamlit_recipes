# Streamlit Recipes

## A project for experimenting with Streamlit and AI agents

This project was developed with Python 3.13 using uv to manage dependencies and the virtual environment.

All of the applications in this project are initially being used with locally downloaded LLMs and accessed via Ollama.
If you have an OpenAI, Anthropic, or other LLM provider subscription, you can easily adapt these applications to use them.

https://github.com/rscarberry-wa/streamlit_recipes

### 1. Simple Ollama Query

Repository path: [simple_ollama_query](simple_ollama_query/)

A simple Streamlit app for querying various Ollama models that have been downloaded to your local Ollama server. Since no chat history 
is maintained, every query is independent of the previous ones. In other words, the LLM has no memory. The point of this 
app is to show how to use Ollama with Streamlit and look at the characteristics of the models.

To run:

1. Install Ollama and start the server either locally or on an accessible server on your network.
2. Download some models on the computer you've installed Ollama. (E.g. `ollama pull llama3:7b`, etc..)
3. Clone this repo and setup your project in the IDE of your choice. I've developed this using PyCharm.
4. Create an .env with contents similar to the following, but with a model you've downloaded to the server and the correct base URL:
```  
OLLAMA_MODEL="gemma3:27b"
OLLAMA_BASE_URL="http://localhost:11434/"
```
5. Install the dependent libraries `streamlit, langchain, langchain-ollama, dotenv`
6. Run `streamlit run simple_ollama_chat/simple_ollama_chat_main.py`
7. Select a model and start chatting.

### 2. Ollama Agent Chat

Repository path: [ollama_agent_chat](ollama_agent_chat/)

Simple Ollama Query did not actually feature an AI agent, since the LLM didn't have tools so that it could take 
autonomous actions. But this application features a web search tool so that it can provide to date answers to questions. 
It can, therefore, be regarded as a true AI agent. It also remembers the thread of conversation, so you can have an 
ongoing chat conversation.

To run:

1. Do all the steps from the previous application.
2. Install the `langchain-tavily` library. It provides the `TavilySearch` tool.
3. Set up a Tavily account, obtain an API key (they have a generous free tier), and place the key in your .env file.
4. Run `streamlit run ollama_agent_chat/ollama_agent_chat_main.py`

Example .env file:
```
OLLAMA_MODEL="gpt-oss:20b"
OLLAMA_BASE_URL="http://localhost:11434/"
TAVILY_API_KEY="<YOUR_API_KEY>"
```

### 3. Multi Modal Agent Chat

Repository path: [multimodal_agent_chat](multimodal_agent_chat/)

This application takes the previous application further by adding audio and image input capabilities to your queries.
It uses an excellent third-party widget named `multimodal-chat-input` (See: [st-chat-input-multimodal](https://github.com/tsuzukia21/st-chat-input-multimodal))

To run:

1. Do all the steps from the previous applications.
2. Install the `st-chat-input-multimodal` library.
3. Run `streamlit run multimodal_agent_chat/multimodal_agent_chat_main.py`

## License

This project is licensed under the Apache License V 2.0.
