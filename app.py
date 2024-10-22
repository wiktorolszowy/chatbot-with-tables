import os

import openai
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session

# from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from werkzeug.utils import secure_filename

from flask_session import Session
from table_bot import CustomPdDataFrameAgentWithContext

# Initialize the Flask app
app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./flask_session"
app.config["UPLOAD_FOLDER"] = "./uploads"
Session(app)

# Ensure the upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def initialize_agent(api_key):
    """
    Initialize the agent outside of the chat function.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)
    # You can use any parameter from the ones described here:
    # https://api.python.langchain.com/en/latest/agents/langchain_experimental.agents.agent_toolkits.pandas.base.create_pandas_dataframe_agent.html
    agent = CustomPdDataFrameAgentWithContext(
        llm=llm,
        verbose=False,
        allow_dangerous_code=True,
        suffix="Think that some column names could contain synonyms of the words in the question.",
    )
    return agent


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    """
    Renders the index page and initializes conversation history if not present.

    This function checks if the 'history' key is present in the session. If not,
    it initializes it as an empty list. It then renders the "index.html" template,
    passing the conversation history to the template.

    Returns:
        A rendered HTML template for the index page with the conversation history.
    """
    if request.method == "POST":
        api_key = request.form.get("api_key")
        if api_key:
            openai.api_key = api_key
            # Validate the API key
            try:
                openai.models.list()  # Simple API call to validate the key
                session["OPENAI_API_KEY"] = api_key
                # FIXME
                # Earlier, saving in session["agent"] led to errors due to serialization of the session data
                global agent
                agent = initialize_agent(api_key)
            except openai.AuthenticationError:
                return render_template("api_key.html", error="Invalid API key")

    if "OPENAI_API_KEY" not in session:
        return render_template("api_key.html")

    # Initialize conversation history if not present
    if "history" not in session:
        session["history"] = []
    if "filenames" not in session:
        session["filenames"] = []

    return render_template("index.html", history=session["history"], filenames=session["filenames"])


@app.route("/upload", methods=["POST"])
def upload() -> str:
    try:
        if "dataframes" not in session:
            session["dataframes"] = []
        if "filenames" not in session:
            session["filenames"] = []

        files = request.files.getlist("files")
        for file in files:
            filename = secure_filename(file.filename)
            if filename == "":
                raise ValueError("No selected file or filename is empty.")
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            if filename.endswith(".csv"):
                df = pd.read_csv(filepath)
            elif filename.endswith(".xls") or filename.endswith(".xlsx"):
                df = pd.read_excel(filepath)
            else:
                raise ValueError("Unsupported file format.")
            session["dataframes"].append(df)
            session["filenames"].append(filename)
        session.modified = True
        return redirect("/")
    except Exception as e:
        app.logger.error(f"Error uploading file: {e}")
        return jsonify({"error": str(e)}), 500


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

    if "dataframes" in session and session["dataframes"]:
        dfs = session["dataframes"]
    else:
        dfs = None

    with agent.inject_dataframe(data=dfs):
        filenames_str = ", ".join(session["filenames"])
        response = agent.invoke(
            message
            + ". In your answer to me refer to the tables using the following names (you know them as df1, df2, etc): "
            + filenames_str
            + ". Consider this chat history: "
            + history_str
        )

    # Update conversation history
    session["history"].append({"question": message, "response": response})
    session.modified = True
    return jsonify({"response": response})


# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
