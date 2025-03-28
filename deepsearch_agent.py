from pydantic_ai import Agent
from pydantic_ai.common_tools.tavily import tavily_search_tool
from dotenv import load_dotenv
import os
from deep_research import Deep_research_engine
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

load_dotenv()
tavily_key=os.getenv('tavily_key')
google_api_key=os.getenv('google_api_key')

llm=GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=google_api_key))






