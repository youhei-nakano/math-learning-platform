# OpenAI API Sandbox

A learning project for building AI applications with the OpenAI API.

## Current Features

* OpenAI API integration using the Responses API
* API key management using environment variables
* Python virtual environment setup

## Tech Stack

* Python
* OpenAI API

## Setup

Create and activate a virtual environment:

```zsh
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```zsh
python -m pip install -r requirements.txt
```

Set the OpenAI API key as an environment variable:

```zsh
read -s "OPENAI_API_KEY?OpenAI API key: "
export OPENAI_API_KEY
echo
```

Run the application:

```zsh
python main.py
```

## Roadmap

* Function Calling
* RAG (Retrieval-Augmented Generation)
* AI Agents
* LangGraph
* MCP
* Mathematical research assistant
