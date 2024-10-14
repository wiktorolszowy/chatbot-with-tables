import os

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from sklearn.datasets import load_diabetes, load_iris

from flask_session import Session
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
    suffix="Think that some column names could contain synonyms of the words in the question.",
)

# %% Make the flask app

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./flask_session"
Session(app)


@app.route("/")
def index() -> str:
    """
    Renders the index page and initializes conversation history if not present.

    This function checks if the 'history' key is present in the session. If not,
    it initializes it as an empty list. It then renders the "index.html" template,
    passing the conversation history to the template.

    Returns:
        A rendered HTML template for the index page with the conversation history.
    """
    # Initialize conversation history if not present
    if "history" not in session:
        session["history"] = []
    return render_template("index.html", history=session["history"])


@app.route("/chat", methods=["POST"])
def chat() -> jsonify:
    """
    Handles incoming chat messages, processes them using an agent, and updates the conversation history.

    This function:
    1. Retrieves JSON data from the request.
    2. Extracts the message from the JSON data.
    3. Injects a DataFrame into the agent's context.
    4. Invokes the agent with the extracted message to get a response.
    5. Updates the session's conversation history with the question and response.
    6. Marks the session as modified.
    7. Returns the response as a JSON object.

    Returns:
        Response: A JSON object containing the agent's response.
    """
    data = request.get_json()
    message = data.get("message")
    # Make a string representation of the conversation history, to be added to the question/message
    history_str = " ".join(
        [f"Question: {entry['question']} Response: {entry['response']}" for entry in session["history"]]
    )
    with agent.inject_dataframe(data=df_iris):
        response = agent.invoke(message + ". Consider this chat history: " + history_str)
    # Update conversation history
    session["history"].append({"question": message, "response": response})
    session.modified = True
    return jsonify({"response": response})


# %% Run the Flask app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
