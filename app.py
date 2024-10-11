# Contact: Wiktor Olszowy, olszowyw@gmail.com

import os

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from sklearn.datasets import load_diabetes, load_iris

from table_bot import CustomPdDataFrameAgentWithContext

# %% Read in the tabular data

df_diabetes = load_diabetes(as_frame=True)["data"]
df_iris = load_iris(as_frame=True)["data"]

# %% Specify the language model
#
# llama3.1 is very basic. Would be better to rely on a larger model, e.g. GPT-4o from OpenAI.

# If you have access to OpenAI's API, you can use GPT-4o, e.g., via `langchain_openai.ChatOpenAI`.
# You need to create file `config.env` and put the key there: `OPENAI_API_KEY=...`
# Wiktor uses his own key and `.gitignore` covers `config.env`. You need to create file `config.env` by yourself.
# And you need to use your own OpenAI API key.
# Wiktor's observations/basic tests show that our agent with GPT-4o is much better than with llama3.1. No surprise.

load_dotenv("config.env")
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
# For llama3.1:
# llm = ChatOllama(model="llama3.1")

# %% Create/initialize the custom agent with context manager

# You can use any parameter from the ones described here:
# https://api.python.langchain.com/en/latest/agents/langchain_experimental.agents.agent_toolkits.pandas.base.create_pandas_dataframe_agent.html

agent = CustomPdDataFrameAgentWithContext(
    llm=llm,
    # Change to True if you want to see some details what the tool does
    verbose=False,
    # This is a risky operation and, actually, should be done in a sandboxed env
    allow_dangerous_code=True,
    agent_type="tool-calling",
    # Basic prompt engineering
    # The language models (both llama3.1 and gpt-4o) sometimes can not identify synonyms (they won't identify the relevant columns in the df).
    suffix="Answer the question without asking me any additional questions. Think that some columns could contain synonyms of the words in the question.",
)

# %% Make the flask app

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message")
    with agent.inject_dataframe(data=df_iris):
        response = agent.invoke(message)
    return jsonify({"response": response["output"]})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
