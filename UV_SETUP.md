# UV Setup Guide

This project uses [uv](https://docs.astral.sh/uv/) as the package manager and virtual environment manager.

## Installation

First, install uv:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.sh | iex"

# Or with pip
pip install uv
```

## Project Setup

1. **Initialize the project and create virtual environment:**
   ```bash
   cd deep_research_agent
   uv sync
   ```
   This will:
   - Create a `.venv` directory with the virtual environment
   - Install all dependencies from `pyproject.toml`
   - Generate a `uv.lock` file for reproducible builds

2. **Activate the virtual environment:**
   ```bash
   # On Unix/macOS
   source .venv/bin/activate
   
   # On Windows
   .venv\Scripts\activate
   ```

3. **Or run commands directly with uv:**
   ```bash
   uv run streamlit run app.py
   uv run python -m pytest
   ```

## Development

- **Install dev dependencies:**
  ```bash
  uv sync --group dev
  ```

- **Add new dependencies:**
  ```bash
  uv add package-name
  uv add --dev package-name  # for dev dependencies
  ```

- **Remove dependencies:**
  ```bash
  uv remove package-name
  ```

- **Update dependencies:**
  ```bash
  uv sync --upgrade
  ```

## Running the Application

```bash
# Using uv run (recommended)
uv run streamlit run app.py

# Or activate venv and run directly
source .venv/bin/activate
streamlit run app.py
```

## Docker

The Dockerfile has been updated to use uv for dependency management. Build and run with:

```bash
docker build -t deep-research-agent .
docker run -p 8501:8501 deep-research-agent
```

## Key Benefits of uv

- **Fast**: Much faster than pip for dependency resolution and installation
- **Reproducible**: Lock files ensure consistent environments
- **Simple**: Single tool for virtual environments and package management
- **Compatible**: Works with existing PyPI packages and requirements.txt files 