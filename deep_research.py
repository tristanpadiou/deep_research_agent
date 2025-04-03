from pydantic_graph import BaseNode, End, GraphRunContext, Graph
from pydantic_ai import Agent
from pydantic_ai.common_tools.tavily import tavily_search_tool
from dataclasses import dataclass
from pydantic import Field, BaseModel
from typing import  List, Dict, Optional
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from dotenv import load_dotenv
import os
from tavily import TavilyClient
from IPython.display import Image, display
import requests
import time


load_dotenv()
google_api_key=os.getenv('google_api_key')
tavily_key=os.getenv('tavily_key')
tavily_client = TavilyClient(api_key=tavily_key)
llm=GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=google_api_key))
pse=os.getenv('pse')

@dataclass
class State:
    query:str
    preliminary_research: str
    research_plan: Dict
    research_results: Dict
    validation : str
    final: Dict

class paragraph(BaseModel):
    title: str = Field(description='the title of the paragraph')
    content: Optional[str] = Field(default_factory=None,description='a paragraph in markdown format, no table or image, if needed else return None')
    


class Paper_layout(BaseModel):
    title: str = Field(description='the title of the paper in markdown format')
    image_url: Optional[str] = Field(default_factory=None,description='the image url if needed else return None')
    paragraphs: List[paragraph]= Field(description='the list of paragraphs of the paper')
    table: Optional[str] = Field(default_factory=None,description='the table if needed else return None')
    references: str = Field(default_factory=None,description='the references (urls) of the paper from the research_results')

paper_layout_agent=Agent(llm, result_type=Paper_layout, system_prompt="generate a paper layout based on the query, preliminary_search, search_results, for the paragraphs only include the title, no content, no image, no table, start with introduction and end with conclusion")
paragraph_gen_agent=Agent(llm, result_type=paragraph, system_prompt="generate a paragraph synthesizing the research_results based on the title")
class PaperGen_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])->End:
        prompt=(f'query:{ctx.state.query}, preliminary_search:{ctx.state.preliminary_research},search_results:{ctx.state.research_results.research_results}')
        result=await paper_layout_agent.run(prompt)
        if ctx.state.research_results.image_url:
            result.data.image_url=ctx.state.research_results.image_url
        if ctx.state.research_results.table:
            result.data.table=ctx.state.research_results.table
        if ctx.state.research_results.references:
            result.data.references=ctx.state.research_results.references
        ctx.state.final=result.data
        data=[]
        for i in ctx.state.final.paragraphs:
            time.sleep(2)
            result=await paragraph_gen_agent.run(f'title:{i.title}, research_results:{ctx.state.research_results.research_results}')
            data.append(result.data)
        ctx.state.final.paragraphs=data
                
        return End(ctx.state.final.model_dump())

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

class Table(BaseModel):
    table: str = Field(description='the table in markdown format')

class Research_results(BaseModel):
    research_results: List[str] = Field(default_factory=None,description='the research results')
    image_url: str = Field(default_factory=None,description='the image url if needed else return None')
    table: str = Field(default_factory=None,description='the table in markdown code if needed else return None')
    references: str = Field(default_factory=None,description='the references (urls) of the research_results')

table_agent=Agent(llm, result_type=Table, system_prompt="generate a detailed table in markdown format based on the research and the query")



class Research_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])->PaperGen_node:
        research_results=Research_results(research_results=[], image_url='', table='', references='')
        
        for i in ctx.state.research_plan.search_queries:
            response = tavily_client.search(i.search_query)
            data=[]
            for i in response.get('results'):
                if i.get('score')>0.50:
                    search_data={'content':i.get('content'),'url':i.get('url')}
                    
                    data.append(search_data.get('url'))
                    research_results.research_results.append(search_data.get('content'))
        research_results.research_results=list(set(research_results.research_results))
        research_results.references=list(set(data))
        research_results.references=', '.join(research_results.references)
        ctx.state.research_results=research_results
        if ctx.state.research_plan.image_search_query:
            image_url=google_image_search(ctx.state.research_plan.image_search_query)
            ctx.state.research_results.image_url=image_url
       
        if ctx.state.research_plan.table:
            result=await table_agent.run(f'research_results:{ctx.state.research_results.research_results},query:{ctx.state.query}')
            ctx.state.research_results.table=result.data.table
        
        
        return PaperGen_node()

class search_query(BaseModel):
    search_query: str = Field(description='the detailed web search query for the research')
    
class Research_plan(BaseModel):
    search_queries: List[search_query] = Field(description='the detailed web search queries for the research')
    table: Optional[str] = Field(default_factory=None,description='if a table is needed, return yes else return None')
    image_search_query: Optional[str] = Field(default_factory=None,description='if image is needed, generate a image search query, optional')

research_plan_agent=Agent(llm, result_type=Research_plan, system_prompt='generate a detailed research plan breaking down the research into smaller parts based on the query and the preliminary search, include a table and image search query if the user wants it')

class Research_plan_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])->Research_node:
        
        prompt=(f'query:{ctx.state.query}, preliminary_search:{ctx.state.preliminary_research}')
        result=await research_plan_agent.run(prompt)
        ctx.state.research_plan=result.data
        return Research_node()
    
    
search_agent=Agent(llm, tools=[tavily_search_tool(tavily_key)], system_prompt="do a websearch based on the query")

class preliminary_search_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State]) -> Research_plan_node:
        prompt = (' Do a preliminary search to get a global idea of the subject that the user wants to do reseach on as well as the necessary informations to do a search on.\n'
                  f'The subject is based on the query: {ctx.state.query}, return the results of the search.')
        result=await search_agent.run(prompt)
        ctx.state.preliminary_research=result.data
        return Research_plan_node()

class Deep_research_engine:
    def __init__(self):
        self.graph=Graph(nodes=[preliminary_search_node, Research_plan_node, Research_node, PaperGen_node])
        self.state=State(query='', preliminary_research='', research_plan=[], research_results=[], validation='', final='')

    async def chat(self,query:str):
        """Chat with the deep research engine,
        Args:
            query (str): The query to search for
        Returns:
            str: The response from the deep research engine
        """
        self.state.query=query
        response=await self.graph.run(preliminary_search_node(),state=self.state)
        return response.output


    def display_graph(self):
        """Display the graph of the deep research engine
        Returns:
            Image: The image of the graph
        """
        image=self.graph.mermaid_image()
        return display(Image(image))

