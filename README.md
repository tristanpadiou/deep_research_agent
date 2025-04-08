# Research Assistant Chatbot

A Streamlit-based research assistant that helps with deep research, quick searches, and paper generation. The application features a chat interface, research paper generation, and table editing capabilities.

## Features

- 💬 Interactive chat interface
- 📄 Research paper generation
- 📊 Editable tables
- 🔍 Deep and quick research capabilities
- 📥 Export to DOCX format

## Prerequisites

- Python 3.12 or higher (Python 3.13 is not yet supported in Docker)
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

1. Clone the repository:
```bash
git clone <repository-url>
cd deep_research_agent
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Unix or MacOS
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run streamlit_app.py
```

The application will be available at `http://localhost:8501`

## Docker Deployment

The Docker setup uses the official Python 3.12 slim image, which comes with Python pre-installed. This means you don't need to install Python separately when using Docker.

1. Build the Docker image:
```bash
docker build -t research-assistant .
```
This will:
- Pull the Python 3.12 slim base image
- Set up the working directory
- Install all required dependencies
- Copy your application code
- Configure the container to run the Streamlit app

2. Run the container:
```bash
docker run -p 8501:8501 --env-file .env research-assistant
```

The application will be available at `http://localhost:8501`

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

3. **Python Environment Issues**
   - Ensure you're using Python 3.11 or higher
   - Try recreating the virtual environment
   - Check for conflicting package versions

## Contributing

Feel free to submit issues and enhancement requests!

## License

[Your License Here]
