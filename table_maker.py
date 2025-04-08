from pydantic_graph import BaseNode, End, GraphRunContext, Graph
from pydantic_ai import Agent
from pydantic_ai.common_tools.tavily import tavily_search_tool
from dataclasses import dataclass
from pydantic import Field, BaseModel
from typing import  List, Dict, Optional, Any
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from dotenv import load_dotenv
import os
from tavily import TavilyClient
from IPython.display import Image, display
import requests

load_dotenv()
google_api_key=os.getenv('google_api_key')
tavily_key=os.getenv('tavily_key')
tavily_client = TavilyClient(api_key=tavily_key)
llm=GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=google_api_key))

@dataclass
class State:
    query:str
    research:List[str]
    table:dict
    preliminary_research:str
    research_plan:List[str]

#define the table row and table schema
class Table_row(BaseModel):
    data: List[str] = Field(description='the data of the row')
class Table(BaseModel): 
    rows: List[Table_row] = Field(description='the rows of the table')
    columns: List[str] = Field(description='the columns of the table')
    

    
class table_maker_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])->End:
        table_agent=Agent(llm, result_type=Table, system_prompt="generate a detailed table in a dictionary format based on the research and the query")
        table=await table_agent.run(f'query:{ctx.state.query}, research:{ctx.state.research}')
        ctx.state.table={'data':[row.data for row in table.data.rows], 'columns':table.data.columns}
        return End(ctx.state.table)
    

class data_research_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])->table_maker_node:
        for i in ctx.state.research_plan:   
            response = tavily_client.search(i.search_query)

            for i in response.get('results'):
                if i.get('score')>0.50:
                    ctx.state.research.append(i.get('content'))
        return table_maker_node()
    


class search_query(BaseModel):
    search_query: str = Field(description='the detailed web search query for the research')
    
class Research_plan(BaseModel):
    search_queries: List[search_query] = Field(description='the detailed web search queries for the research')

research_plan_agent=Agent(llm, result_type=Research_plan, system_prompt='generate a detailed research plan breaking down the research into smaller parts based on the query and the preliminary search')

class Research_plan_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])->data_research_node:
        
        prompt=(f'query:{ctx.state.query}, preliminary_search:{ctx.state.preliminary_research}')
        result=await research_plan_agent.run(prompt)
        ctx.state.research_plan=result.data.search_queries
        return data_research_node()

class preliminary_search_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State]) -> Research_plan_node:
        search_agent=Agent(llm, tools=[tavily_search_tool(tavily_key)], system_prompt="do a websearch based on the query")
        prompt = (' Do a preliminary search to get a global idea of the subject that the user wants to do reseach on as well as the necessary informations to do a search on.\n'
                  f'The subject is based on the query: {ctx.state.query}, return the results of the search.')
        result=await search_agent.run(prompt)
        ctx.state.preliminary_research=result.data
        return Research_plan_node()

    
class table_maker_engine:
    def __init__(self):
        self.graph=Graph(nodes=[preliminary_search_node, Research_plan_node, data_research_node, table_maker_node])
        self.state=State(query='', research=[], table={}, preliminary_research='', research_plan=[])

    async def chat(self,query:str):
        """Chat with the table maker engine,
        Args:
            query (str): The query to search for
        Returns:
            str: The response from the table maker engine
        """
        self.state.query=query
        response=await self.graph.run(preliminary_search_node(),state=self.state)
        return response.output
    
    def display_graph(self):
        """Display the graph of the table maker engine
        Returns:
            Image: The image of the graph
        """
        image=self.graph.mermaid_image()
        return display(Image(image))
