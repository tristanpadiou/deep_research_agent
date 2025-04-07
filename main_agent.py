from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.tavily import tavily_search_tool
from pydantic_ai.messages import ModelMessage
from dotenv import load_dotenv
import os
from pydantic import Field, BaseModel
from typing import Dict, List, Any
from deep_research import Deep_research_engine
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from dataclasses import dataclass
from typing import Optional
from spire.doc import Document,FileFormat
from spire.doc.common import *
import requests
from table_maker import table_maker_engine
from PIL import Image
from io import BytesIO, StringIO
import tempfile
import pandas as pd

load_dotenv()
tavily_key=os.getenv('tavily_key')
google_api_key=os.getenv('google_api_key')
pse=os.getenv('pse')

llm=GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=google_api_key))


@dataclass
class Deps:
    deep_search_results:dict
    quick_search_results:list[str]
    table_data:dict
    



async def deep_research_agent(ctx:RunContext[Deps], query:str):
    """
    This function is used to do a deep research on the web for information on a complex query, generates a report or a paper.
    Args:
        query (str): The query to search for
    Returns:
        str: The result of the search
    """
    deepsearch=Deep_research_engine()
    res=await deepsearch.chat(query)
    ctx.deps.deep_search_results=res
    ctx.deps.table_data=res.get('table')
    return str(res)

quick_search_agent=Agent(llm,tools=[tavily_search_tool(tavily_key)])
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
    return str(res.data)


def google_image_search(query:str):
  """Search for images using Google Custom Search API
  args: query
  return: image url
  """
  # Define the API endpoint for Google Custom Search
  url = "https://www.googleapis.com/customsearch/v1"

  params = {
      "q": query,
      "cx": pse,
      "key": google_api_key,
      "searchType": "image",  # Search for images
      "num": 1  # Number of results to fetch
  }

  # Make the request to the Google Custom Search API
  response = requests.get(url, params=params)
  data = response.json()

  # Check if the response contains image results
  if 'items' in data:
      # Extract the first image result
      image_url = data['items'][0]['link']
      return image_url
  


async def research_editor_tool(ctx: RunContext[Deps], query:str):
    """
    Use this tool to edit the deep search result to make it more accurate following the query's instructions.
    This tool can modify paragraphs, image_url. For image_url, you need to give the query to search for the image.
    Args:
        query (str): The query containing instructions for editing the deep search result
    Returns:
        str: The edited and improved deep search result
    """
    @dataclass
    class edit_route:
        paragraph_number:Optional[int] = Field(default_factory=None, description='the number of the paragraph to edit, if the paragraph is not needed to be edited, return None')
        route: str = Field(description='the route to the content to edit, either paragraphs, image_url')

 
   
    paper_dict={'title':ctx.deps.deep_search_results.get('title'),
                                'image_url':ctx.deps.deep_search_results.get('image_url') if ctx.deps.deep_search_results.get('image_url') else 'None',
                                'paragraphs_title':{num:paragraph.get('title') for num,paragraph in enumerate(ctx.deps.deep_search_results.get('paragraphs'))}, 
                                'table':ctx.deps.deep_search_results.get('table') if ctx.deps.deep_search_results.get('table') else 'None',
                                'references':ctx.deps.deep_search_results.get('references')}
    
    route_agent=Agent(llm,result_type=edit_route, system_prompt="you decide the route to the content to edit based on the query's instructions and the paper_dict, either paragraphs, image_url")
    route=await route_agent.run(f'query:{query}, paper_dict:{paper_dict}')
    contents=ctx.deps.deep_search_results
 
  
    @dataclass
    class Research_edits:
        edits:str = Field(description='the edits')
    editor_agent=Agent(llm,tools=[google_image_search],result_type=Research_edits, system_prompt="you are an editor, you are given a query, some content to edit, and maybe a quick search result (optional), you need to edit the deep search result to make it more accurate following the query's instructions, return only the edited content, no comments")
    if route.data.route=='paragraphs':
        content=contents.get('paragraphs')[route.data.paragraph_number]['content']
        res=await editor_agent.run(f'query:{query}, content:{content}, quick_search_results:{ctx.deps.quick_search_results if ctx.deps.quick_search_results else "None"}')
        ctx.deps.deep_search_results['paragraphs'][route.data.paragraph_number]['content']=res.data.edits
    if route.data.route=='image_url':
        content=contents.get('image_url')
        res=await editor_agent.run(f'query:{query}, content:{content}, quick_search_results:{ctx.deps.quick_search_results if ctx.deps.quick_search_results else "None"}')
        ctx.deps.deep_search_results['image_url']=res.data.edits

    
    return str(ctx.deps.deep_search_results)


async def Table_agent(ctx: RunContext[Deps], query:str):
    """
    Use this tool to create a table, edit a table or add a table to the deep search result.
    Args:
        query (str): The query to create a table, edit a table or add a table to the deep search result
    Returns:
        dict: The table
    """
    @dataclass
    class route:
        route: str = Field(description='the route to the content to edit, either create_table, edit_table, or add_table_to_paper')
    route_agent=Agent(llm,result_type=route, system_prompt="you decide the route to the content to edit based on the query's instructions, return only the route, either create_table, edit_table, or add_table_to_paper")
    route=await route_agent.run(f'query:{query}')


    if route.data.route=='create_table':
        table_maker=table_maker_engine()
        table=await table_maker.chat(query)
        ctx.deps.table_data=table
        return str(table)
    
    if route.data.route=='edit_table':
        table=ctx.deps.table_data
        class Table_row(BaseModel):
            data: List[str] = Field(description='the data of the row')
        class Table(BaseModel): 
            rows: List[Table_row] = Field(description='the rows of the table')
            columns: List[str] = Field(description='the columns of the table')

        table_agent=Agent(llm, result_type=Table, system_prompt="edit the table based on the query's instructions, the research results (if any) and the quick search results(if any)")
        generated_table=await table_agent.run(f'query:{query}, table:{table}, research:{ctx.deps.deep_search_results if ctx.deps.deep_search_results else "None"}, quick_search_results:{ctx.deps.quick_search_results if ctx.deps.quick_search_results else "None"}')
        ctx.deps.table_data={'data':[row.data for row in generated_table.data.rows], 'columns':generated_table.data.columns}
        return str(ctx.deps.table_data)
    
    if route.data.route=='add_table_to_paper':
        ctx.deps.deep_search_results['table']=ctx.deps.table_data
        return str(ctx.deps.deep_search_results)

@dataclass
class Message_state:
    messages: list[ModelMessage]



class Main_agent:
    def __init__(self):
        self.agent=Agent(llm, system_prompt="you are a research assistant, you are given a query, leverage what tool(s) to use but do not use the presentation agent unless the user asks for it,\
                          always show the output of the tools, except for the presentation agent",
                          tools=[deep_research_agent,research_editor_tool,quick_research_agent,Table_agent])
        self.deps=Deps( deep_search_results=[], quick_search_results=[], table_data={})
        self.memory=Message_state(messages=[])

    async def chat(self, query:str):
        result = await self.agent.run(query,deps=self.deps, message_history=self.memory.messages)
        self.memory.messages=result.all_messages()
        return result.data
    
    def reset(self):
        self.memory.messages=[]
        self.deps=Deps( deep_search_results=[], quick_search_results=[])

