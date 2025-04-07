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
        response = tavily_client.search(ctx.state.query)

        for i in response.get('results'):
            if i.get('score')>0.50:
                ctx.state.research.append(i.get('content'))
        return table_maker_node()
    

class table_maker_engine:
    def __init__(self):
        self.graph=Graph(nodes=[data_research_node, table_maker_node])
        self.state=State(query='', research=[], table={})

    async def chat(self,query:str):
        """Chat with the table maker engine,
        Args:
            query (str): The query to search for
        Returns:
            str: The response from the table maker engine
        """
        self.state.query=query
        response=await self.graph.run(data_research_node(),state=self.state)
        return response.output
    
    def display_graph(self):
        """Display the graph of the table maker engine
        Returns:
            Image: The image of the graph
        """
        image=self.graph.mermaid_image()
        return display(Image(image))
