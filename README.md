# Research Assistant Chatbot

A Streamlit-based research assistant that helps with deep research, quick searches, and paper generation. The application features a chat interface, research paper generation, and table editing capabilities.

## Features

- 💬 Interactive chat interface
- 📄 Research paper generation
- 📊 Editable tables
- 🔍 Deep and quick research capabilities
- 📥 Export to DOCX format

## Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (optional, for containerized deployment)
- API keys for:
  - Google API (for Gemini and Custom Search)
  - Tavily API

## Environment Setup

1. Create a `.env` file in the root directory with the following variables:
```env
google_api_key=your_google_api_key
tavily_key=your_tavily_api_key
pse=your_programmable_search_engine_id
```

## Local Installation

1. Install uv if you haven't already:
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.sh | iex"

# Or with pip
pip install uv
```

2. Clone the repository:
```bash
git clone <repository-url>
cd deep_research_agent
```

3. Install dependencies and create virtual environment:
```bash
uv sync
```
This will automatically:
- Create a `.venv` directory with the virtual environment
- Install all dependencies from `pyproject.toml`
- Generate a `uv.lock` file for reproducible builds

4. Run the application:
```bash
# Using uv run (recommended)
uv run streamlit run app.py

# Or activate environment and run directly
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Docker Deployment

The Docker setup uses uv for fast and reliable dependency management.

1. Build the Docker image:
```bash
docker build -t research-assistant .
```
This will:
- Use the official uv Docker image with Python 3.13
- Set up the working directory
- Install all dependencies using uv
- Copy your application code
- Configure the container to run the Streamlit app

2. Run the container:
```bash
docker run -p 8501:8501 --env-file .env research-assistant
```

The application will be available at `http://localhost:8501`

## Development

### Adding Dependencies
```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name
```

### Updating Dependencies
```bash
# Update all dependencies
uv sync --upgrade

# Update a specific dependency
uv add package-name@latest
```

### Running Tests
```bash
uv run python -m pytest
```

### Code Formatting
```bash
uv run black .
uv run flake8 .
uv run mypy .
```

## Usage Guide

### Chat Interface
- Click the 💬 button to open the chat assistant
- Type your research questions or requests
- Use the 🔄 button to reset the chat

### Research Paper
- Click the 📄 button to view the generated research paper
- Use the 📥 button to download the paper as a DOCX file

### Table Editor
- Click the 📊 button to open the table editor
- Edit the table as needed
- Click 💾 to update the table in the research paper

## Tips for Best Results

1. Be specific in your questions
2. Use clear and concise language
3. Focus on one topic at a time
4. Use the table editor to organize data
5. Export your research paper when complete

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure all API keys are correctly set in the `.env` file
   - Check that the keys have the necessary permissions

2. **Docker Issues**
   - Make sure Docker is running
   - Check that port 8501 is not in use
   - Verify the `.env` file is properly mounted

3. **uv Environment Issues**
   - Try recreating the virtual environment: `rm -rf .venv && uv sync`
   - Ensure you have the latest version of uv: `uv self update`
   - Check for conflicting package versions in `uv.lock`

4. **Python Version Issues**
   - Ensure you're using Python 3.13 or higher
   - uv will automatically use the correct Python version specified in `pyproject.toml`

## Why uv?

This project uses [uv](https://docs.astral.sh/uv/) as the package manager for several benefits:
- **Fast**: Much faster than pip for dependency resolution and installation
- **Reproducible**: Lock files ensure consistent environments across all machines
- **Simple**: Single tool for virtual environments and package management
- **Reliable**: Better dependency resolution and conflict handling

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License
