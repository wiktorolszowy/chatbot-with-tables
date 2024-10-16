# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: venv
#     language: python
#     name: python3
# ---

# ### Import relevant packages and read in the tabular data

# +
import os

from dotenv import load_dotenv

# from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from sklearn.datasets import load_diabetes, load_iris

from table_bot import CustomPdDataFrameAgentWithContext

# from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

df_diabetes = load_diabetes(as_frame=True)["data"]
df_iris = load_iris(as_frame=True)["data"]
# -

# ### Specify the language model
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

# ### Create/initialize the custom agent with context manager

# You can use any parameter from the ones described here:
# https://api.python.langchain.com/en/latest/agents/langchain_experimental.agents.agent_toolkits.pandas.base.create_pandas_dataframe_agent.html

agent = CustomPdDataFrameAgentWithContext(
    llm=llm,
    # Change to True if you want to see some details what the tool does
    verbose=False,
    # This is a risky operation and, actually, should be done in a sandboxed env
    allow_dangerous_code=True,
    # Basic prompt engineering
    # The language models (both llama3.1 and gpt-4o) sometimes can not identify synonyms (they won't identify the relevant columns in the df).
    suffix="Answer the question without asking me any additional questions. Think that some column names could contain synonyms of the words in the question.",
)

# ### Use the context manager to inject the DataFrame and invoke the agent

with agent.inject_dataframe(data=[df_iris, df_diabetes]):
    # response = agent.invoke("Is there a link between age and the Body Mass Index?")
    # response = agent.invoke("Can you please repeat your statement?")
    # response = agent.invoke("What was your last response?")
    # response = agent.invoke("What is the weakest link in this data?")
    response = agent.invoke("what are the sizes of these dataframes?")
    print(response)

# # Checking the agent directly: without the context manager and without the cache
# agent = create_pandas_dataframe_agent(llm, [df_iris, df_diabetes], allow_dangerous_code=True, agent_type="tool-calling")
# response = agent.invoke("what are the sizes of these dataframes?")
# print(response)
