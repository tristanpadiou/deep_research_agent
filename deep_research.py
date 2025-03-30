from pydantic_graph import BaseNode, End, GraphRunContext, Graph
from pydantic_ai import Agent
from pydantic_ai.common_tools.tavily import tavily_search_tool
from dataclasses import dataclass
from pydantic import Field
from typing import  List
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from dotenv import load_dotenv
import os
from tavily import TavilyClient
from IPython.display import Image, display


load_dotenv()
google_api_key=os.getenv('google_api_key')
tavily_key=os.getenv('tavily_key')
tavily_client = TavilyClient(api_key=tavily_key)
llm=GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=google_api_key))

@dataclass
class State:
    query:str
    preliminary_research: str
    research_plan: List
    research_results: List
    validation : str
    final: str


search_agent=Agent(llm, tools=[tavily_search_tool(tavily_key)], system_prompt="do a websearch based on the query")
paper_gen_agent=Agent(llm, system_prompt="syntheze the information based on the query, ether write a paper or a report, add all the necessary informations, preliminary_search, and search_results and provide a detailed analysis of the information, include url sources")



class PaperGen_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])->End:
        prompt=(f'Based on this query:{ctx.state.query}, and this preliminary_search:{ctx.state.preliminary_research}, and the search_results:{ctx.state.research_results}, synthesize the information write a paper or a report, include the url sources.')
        result=await paper_gen_agent.run(prompt)
        ctx.state.final=result.data
        return End(result.data)

class Research_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])->PaperGen_node:
        data=[]
        for i in ctx.state.research_plan:
            response = tavily_client.search(i.search_query)
            search_results=[]
            for i in response.get('results'):
                if i.get('score')>0.50:
                    search_data={'content':i.get('content'),'url':i.get('url')}
                    search_results.append(search_data)
            data.append(search_results)
        ctx.state.research_results.append(data)
        return PaperGen_node()
@dataclass
class Tasks:
    task: str = Field(description='the task to complete')
    search_query: str = Field(description='the detailed web search query based on the task')
@dataclass
class Research_plan:
    Plan: List[Tasks]
research_plan_agent=Agent(llm, result_type=Research_plan, system_prompt='generate a research plan based on the query and the preliminary search')

class Research_plan_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])->Research_node:
        
        prompt=(f'generate a detailed research plan breaking down the research into smaller parts based on this query:{ctx.state.query} and this preliminary_search:{ctx.state.preliminary_research}')
        result=await research_plan_agent.run(prompt)
        ctx.state.research_plan=result.data.Plan
        return Research_node()

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

