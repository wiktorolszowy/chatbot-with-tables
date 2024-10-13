# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Install pipx, uv
RUN apt-get update && \
    apt-get install -y pipx git && \
    pipx ensurepath && \
    pipx install uv

# Set the working directory in the container
WORKDIR /app

# Copy the pyproject.toml file into the container
COPY pyproject.toml .

# Create and activate a virtual environment, then install dependencies. All using uv.
RUN /root/.local/bin/uv venv && \
    . .venv/bin/activate && \
    /root/.local/bin/uv pip install -r pyproject.toml && \
    /root/.local/bin/uv lock

# Copy the rest of the application code into the container
COPY . .

# Set the environment variable to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# It seems that without this line, the venv is not activated. Very strange. FIXME
RUN /root/.local/bin/uv run python -c "import pandas; print(pandas.__version__)"

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]