from pydantic_ai import Agent
from pydantic_graph import BaseNode, GraphRunContext, End, Graph
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.models.gemini import GeminiModel
from dotenv import load_dotenv
import os
from pydantic import Field
from typing import  List, Dict, Optional
from dataclasses import dataclass
from IPython.display import Image, display  
import time
import requests
load_dotenv()

google_api_key=os.getenv('google_api_key')
pse=os.getenv('pse')
llm=GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=google_api_key))

@dataclass
class State:
    instruction: str
    presentation_style: str
    research: str
    presentation_plan: List[Dict]
    presentation: Dict
    html_presentation: str


@dataclass  
class html_schema:
    html: str

html_agent=Agent(llm, result_type=html_schema, system_prompt='generate a html presentation based on the presentation')

class html_presentation(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])-> End:
        for key in ctx.state.presentation.keys():
            time.sleep(2)
            page=ctx.state.presentation[key]
            result=await html_agent.run(f'generate a html presentation based on the page schema and user defined style {ctx.state.presentation_style}, include line breaks so it can be displayed in a presentation: {page}')
            ctx.state.html_presentation[key]=result.data.html

        return End(ctx.state.html_presentation)


class clean_up_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])-> html_presentation:
        page_number=1
        for task in ctx.state.presentation_plan.tasks:
            ctx.state.presentation[f'page_{page_number}']={'title':task.text_data.Text_title, 'text':task.text_data.Text_content,'image_title':task.image_data.image_title,'image':task.image_data.image_url}
            page_number+=1
        return html_presentation()


text_extraction_agent=Agent(llm, system_prompt='extract the text from the reaserch based on the instructions')

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
  

class step_execution_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])-> clean_up_node:
        for task in ctx.state.presentation_plan.tasks:
            time.sleep(2)
            if task.image_data:
                task.image_data.image_url=google_image_search(task.image_data.image_title)
            if task.text_data:
                result=await text_extraction_agent.run(f'extract the text from the research: {ctx.state.research} based on the instructions: {task.text_data.Text_to_extract}')
                task.text_data.Text_content=result.data
        
        return clean_up_node()

@dataclass
class image:
    image_title: str = Field(description='the image title')
    image_position: int = Field(description='the image position in the presentation')
    image_url: str = None

@dataclass
class text:
    Text_to_extract: str = Field(description=' a description of the text to extract from the research')
    Text_title: str = Field(description='the text title')
    Text_position: int = Field(description='the text position in the presentation')
    Text_content: str = None

@dataclass
class steps:
    image_data: Optional[image] = Field(description='the image data, or empty if no image is needed')
    text_data: text = Field(description='the text data')

@dataclass
class Presentation_plan:
    tasks: List[steps] = Field(description='the steps to complete')


presentation_plan_agent=Agent(llm, result_type=Presentation_plan, system_prompt='generate a presentation plan based on the research and instruction (if any), choose wether to use images or not for each step')
        
class Presentation_plan_node(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State])->step_execution_node:
        prompt=f'generate a presentation plan based on the research: {ctx.state.research} and instruction: {ctx.state.instruction} (if any), choose wether to use images or not for each step, make sure that the sources URLsare included in the presentation'
        result=await presentation_plan_agent.run(prompt)
        ctx.state.presentation_plan=result.data
        return step_execution_node()
    

class Presentation_gen:
    def __init__(self):
        self.graph=Graph(nodes=[Presentation_plan_node, step_execution_node, clean_up_node, html_presentation])
        self.state=State(research='', presentation_plan=[], presentation={}, html_presentation={}, presentation_style='', instruction='')

    async def chat(self,research:str, presentation_style:str, instruction:str):
        """Chat with the presentation generator,
        Args:
            research (str): The research to generate a presentation for
        Returns:
            str: The response from the presentation generator
        """
        self.state.research=research
        self.state.presentation_style=presentation_style
        self.state.instruction=instruction
        response=await self.graph.run(Presentation_plan_node(),state=self.state)
        return response.output


    def display_graph(self):
        """Display the graph of the deep research engine
        Returns:
            Image: The image of the graph
        """
        image=self.graph.mermaid_image()
        return display(Image(image))