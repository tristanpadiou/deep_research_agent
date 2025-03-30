from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.tavily import tavily_search_tool
from dotenv import load_dotenv
import os
from deep_research import Deep_research_engine
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from dataclasses import dataclass

load_dotenv()
tavily_key=os.getenv('tavily_key')
google_api_key=os.getenv('google_api_key')

llm=GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=google_api_key))

deepsearch=Deep_research_engine()

@dataclass
class Deps:

    deep_search_results:list[str]
    quick_search_results:list[str]
    edited_deep_search_result:str

agent=Agent(llm, system_prompt="you are a research assistant, you are given a query, decide if you need to do a deep research or a quick search, if you need to do a deep research, use the deep_research_agent tool, if you need to do a quick search, use the search_agent tool, if you need to edit the deep search result, use the editor_agent tool")

@agent.tool
async def deep_research_agent(ctx:RunContext[Deps], query:str):
    """
    This function is used to do a deep research on the web for information on a complex query, generates a report or a paper.
    Args:
        query (str): The query to search for
    Returns:
        str: The result of the search
    """
    res=await deepsearch.chat(query)
    ctx.deps.deep_search_results.append(res)
    return res

quick_search_agent=Agent(llm,tools=[tavily_search_tool(tavily_key)])
@agent.tool
async def quick_research_agent(ctx: RunContext[Deps], query:str):
    """
    This function is used to do a quick search on the web for information on a given query.
    Args:
        query (str): The query to search for
    Returns:
        str: The result of the search
    """
    res=await quick_search_agent.run(query)
    ctx.deps.quick_search_results.append(res.data)
    return res.data
    
editor_agent=Agent(llm, system_prompt="you are an editor, you are given a query, a deep search result(s), and maybe quick search result(s) (optional), you need to edit the deep search result to make it more accurate following the query's instructions")

@agent.tool
async def editor_agent(ctx: RunContext[Deps], query:str):
    """
    This function is used to edit the deep search result to make it more accurate following the query's instructions.
    Args:
        query (str): The query containing instructions for editing the deep search result
    Returns:
        str: The edited and improved deep search result
    """
    res=await editor_agent.run(f'query:{query}, deep_search_result:{ctx.deps.deep_search_results}, quick_search_result:{ctx.deps.quick_search_results}')
    ctx.deps.edited_deep_search_result=res
    return res



class Main_agent:
    def __init__(self):
        self.agent=agent
        self.deps=Deps(deep_search_results=[], quick_search_results=[],edited_deep_search_result="")

    async def chat(self, query:str):
        response=await self.agent.run(query,deps=self.deps)
        return response.data
