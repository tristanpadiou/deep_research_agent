from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.tavily import tavily_search_tool
from pydantic_ai.messages import ModelMessage
from dotenv import load_dotenv
import os
from pydantic import Field
from deep_research import Deep_research_engine
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from dataclasses import dataclass
from presentation_generator import Presentation_gen
from typing import Optional

load_dotenv()
tavily_key=os.getenv('tavily_key')
google_api_key=os.getenv('google_api_key')

llm=GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=google_api_key))

deepsearch=Deep_research_engine()
presentation=Presentation_gen()

@dataclass
class Deps:
    deep_search_results:list[str]
    quick_search_results:list[str]
    edited_deep_search_result:str
    presentation_slides:dict

agent=Agent(llm, system_prompt="you are a research assistant, you are given a query, leverage what tool(s) to use, always show the output of the tools, except for the presentation agent")

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
    
editor_agent=Agent(llm, system_prompt="you are an editor, you are given a query, a deep search result, and maybe a quick search result (optional), you need to edit the deep search result to make it more accurate following the query's instructions")

@agent.tool
async def research_editor_tool(ctx: RunContext[Deps], query:str):
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

@agent.tool
async def presentation_agent(
    ctx: RunContext[Deps],
    style: Optional[str] = "professional",
    instruction: Optional[str] = 'None'
) -> dict:
    """
    Generate a presentation based on the deep search result.

    Args:
        style: Presentation style (default: "professional")
        instruction: Additional instructions for presentation generation (default: None)

    Returns:
        dict: The presentation slides
    """
    search_content = (ctx.deps.edited_deep_search_result 
                     if ctx.deps.edited_deep_search_result 
                     else ctx.deps.deep_search_results[0])
    
    res = await presentation.chat(search_content, style=style, instruction=instruction)
    ctx.deps.presentation_slides = res
    return res

@dataclass
class page_edit:
    edits: str = Field(description='the edits to make to the page in html format')

page_editor=Agent(llm, result_type=page_edit, system_prompt='you are a page editor, edit the mentionned page(s) based on the instructions.')

@agent.tool
async def page_editor_tool(ctx: RunContext[Deps], page_number: int, instructions: str):
    """
    This function is used to edit the mentionned page(s) based on the instructions.
    Args:
        page_number (int): The number of the page to edit
        instructions (str): The instructions for the page edits
    Returns:
        str: The edited page
    """
    result=await page_editor.run(f'page:{ctx.deps.presentation_slides[f"page_{page_number}"]}, instructions:{instructions}')
    ctx.deps.presentation_slides[f"page_{page_number}"]=result.data.edits
    return result.data.edits

deps=Deps( deep_search_results=[], quick_search_results=[],edited_deep_search_result="", presentation_slides={})


@dataclass
class message_state:
    messages: list[ModelMessage]

memory=message_state(messages=[])

class Main_agent:
    def __init__(self):
        self.agent=agent
        self.deps=deps
        self.memory=memory

    async def chat(self, query:str):
        result = await self.agent.run(query,deps=self.deps, message_history=self.memory.messages)
        self.memory.messages=result.all_messages()
        return result.data