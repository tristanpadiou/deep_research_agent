import streamlit as st
import pandas as pd
from main_agent import Main_agent
import asyncio
import tempfile
import os
from PIL import Image
from io import BytesIO
import requests
from spire.doc import Document, FileFormat
import nest_asyncio
import platform
from dataclasses import dataclass

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Create event loop
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

test_data={'title': 'Sunday App and Stripe: A Payment Strategy for Restaurants',
 'image_url': 'https://www.menutiger.com/_next/image?url=http%3A%2F%2Fcms.menutiger.com%2Fwp-content%2Fuploads%2F2023%2F07%2Fseamless-stripe-payment-integration-for-restaurants-2.jpg&w=2048&q=75',
 'paragraphs': [{'title': 'Introduction',
   'content': 'Sunday is a payment solution designed to streamline the restaurant experience. Co-founded in April 2021 by Christine de Wendel, Victor Lugger, and Tigrane Seydoux, it aims to address inefficiencies in the restaurant industry by simplifying payments through QR code technology, allowing customers to quickly access their bill, split it, add a tip, and pay in seconds. Integrated with existing POS systems and partnering with payment providers like Stripe and Checkout.com, Sunday also offers features such as digital menus with customizable options, order and pay capabilities, and tools to enhance online reputation and customer engagement for restaurants.'},
  {'title': "Sunday's Payment Strategy",
   'content': "Sunday's payment strategy focuses on streamlining the payment process in restaurants through its QR code-based system, enabling customers to pay quickly and efficiently. This approach not only simplifies payments but also reduces processing fees for restaurants through partnerships with companies like Stripe and Checkout.com. The company's payment solution is designed to integrate seamlessly with existing POS systems, offering additional features such as digital menus, order and pay capabilities, and tools to improve online reputation and customer engagement."},
  {'title': 'Partnership with Stripe',
   'content': 'On Wednesday, Sunday announced its new Order & Pay capabilities and its partnership with Stripe, which has allowed it to reduce processing fees for restaurants by an average of 0.5%. Through Stripe, Sunday processes payments via a QR code at the table, which allows customers to pay, split the bill, and add a tip quickly. Sunday is also negotiating with payment providers for better rates.'},
  {'title': 'Stripe Integration and Fee Reduction',
   'content': 'Sunday leverages Stripe to process payments, utilizing a QR code system for customer convenience. This partnership has enabled Sunday to reduce processing fees for restaurants by an average of 0.5%.'},
  {'title': 'Benefits for Restaurants',
   'content': 'Sunday offers numerous benefits for restaurants by leveraging its technology and partnerships, including Stripe. Restaurants using Sunday can experience increased efficiency through streamlined payment processes and order and pay capabilities. Sunday also helps restaurants collect valuable data and analytics, including customer insights and business analytics, which can be used to improve operations and enhance customer experience. Additionally, the integration with Stripe reduces processing fees, benefiting restaurant finances.'},
  {'title': 'Conclusion',
   'content': 'In conclusion, Sunday has significantly impacted restaurant payments by streamlining the payment process and reducing processing fees through its partnership with Stripe. This collaboration has enabled restaurants to enhance efficiency, improve customer experiences, and gain valuable data insights, positioning Sunday as a key player in revolutionizing the restaurant industry.'}],
 'table': {'data': [['App Functionality',
    'Access bill and pay in two clicks, browse the full menu.'],
   ['Payment Processing', 'Payments processed by Stripe.'],
   ['Stripe Agreement Benefit',
    'Reduced processing fees for restaurants by an average of 0.5%.'],
   ['Restaurant Benefits',
    'More tips, more reviews, and more data for restaurants. Increased order and average basket size.'],
   ['Point of Sale Integration',
    'Works seamlessly with existing POS systems.'],
   ['Payment Method', 'Guests scan a QR code to pay.'],
   ['Additional Features',
    'Digital menu with customizable features (scheduling, tags, extras). Options to split the bill and tip.']],
  'columns': ['Aspect', 'Details']},
 'references': 'https://sundayapp.com/2024-recap-how-sunday-revolutionized-restaurant-payments/, https://sundayapp.com/blog/, https://www.checkout.com/case-studies/sunday-brings-the-ease-of-online-payments-to-the-offline-dining-experience'}

@dataclass
class Research_paper_test:
    test_data:dict

test_paper=Research_paper_test
test_paper.test_data=test_data


# Initialize the agent
agent = Main_agent()

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'table_data' not in st.session_state:
    st.session_state.table_data = {}
if 'quick_search_results' not in st.session_state:
    st.session_state.quick_search_results = []
if 'research_paper' not in st.session_state:
    st.session_state.research_paper = {}

if 'agent_memory' not in st.session_state:
    st.session_state.agent_memory = []

if 'loop' not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

agent.deps.deep_search_results = st.session_state.research_paper
agent.deps.quick_search_results = st.session_state.quick_search_results
agent.deps.table_data = st.session_state.table_data
agent.memory.messages = st.session_state.agent_memory

def paper_to_markdown(paper: dict) -> str:
    """Convert a paper dictionary into a markdown string."""
    markdown = []
    
    # Add title
    markdown.append(f"# {paper.get('title')}")
    markdown.append("\n\n")
    if paper.get('image_url'):
        markdown.append(f"![Image]({paper.get('image_url')})\n")
        markdown.append("\n\n")
    
    # Add body sections
    for section in paper.get('paragraphs', []):
        markdown.append(f"## {section.get('title')}\n")
        if section.get('content'):
            markdown.append(section.get('content'))
            markdown.append("\n")
        markdown.append("\n\n")
    
    if paper.get('table'):
        try:
            markdown.append(pd.DataFrame(data=paper.get('table')['data'], 
                                      columns=paper.get('table')['columns']).to_markdown())
        except:
            markdown.append(pd.DataFrame(paper.get('table')).to_markdown())
        markdown.append("\n\n")
    
    # Add references
    markdown.append("## References\n")
    markdown.append(str(paper.get('references')))
    
    return "".join(markdown)

def download_as_docx(paper: dict) -> str:
    """Convert a paper dictionary into a DOCX file."""
    def temp_image_file(url: str):
        image = requests.get(url)
        image = Image.open(BytesIO(image.content))
        with tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False) as temp_file:
            image.save(temp_file.name)
            image_file_path = temp_file.name
        return image_file_path
    if paper.get('image_url'):
        image_path = temp_image_file(paper.get('image_url'))
    else:
        image_path = None

    # Prepare markdown
    markdown = []
    
    # Add title
    markdown.append(f"# {paper.get('title')}")
    markdown.append("\n\n")
    if image_path:
        markdown.append(f"![Image]({image_path})\n")
        markdown.append("\n\n")
    
    # Add body sections
    for section in paper.get('paragraphs', []):
        markdown.append(f"## {section.get('title')}\n")
        if section.get('content'):
            markdown.append(section.get('content'))
            markdown.append("\n")
        markdown.append("\n\n")
    
    if paper.get('table'):
        try:
            markdown.append(pd.DataFrame(data=paper.get('table')['data'], 
                                      columns=paper.get('table')['columns']).to_markdown())
        except:
            markdown.append(pd.DataFrame(paper.get('table')).to_markdown())
        markdown.append("\n\n")
    
    # Add references
    markdown.append("## References\n")
    markdown.append(str(paper.get('references')))
    
    markdown_str = "".join(markdown)
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
        temp_file.write(markdown_str)
        temp_file_path = temp_file.name

    # Create a new document and load from the temporary files
    document = Document()
    document.LoadFromFile(temp_file_path)

    # Save as DOCX
    output_path = "output.docx"
    document.SaveToFile(output_path, FileFormat.Docx)

    # Clean up temporary files
    os.unlink(temp_file_path)
    if image_path:
        os.unlink(image_path)
    
    return output_path

async def process_query(query: str):
    """Process a user query and update the research paper."""
    response = await agent.chat(query)
    st.session_state.chat_history.append({"role": "user", "content": query})
    st.session_state.chat_history.append({"role": "assistant", "content": str(response)})
    st.session_state.agent_memory = agent.memory.messages
    # Update research paper if available
    if agent.deps.deep_search_results:
        st.session_state.research_paper = agent.deps.deep_search_results
        st.session_state.table_data = agent.deps.table_data
    if agent.deps.table_data:
        st.session_state.table_data = agent.deps.table_data
    if agent.deps.quick_search_results:
        st.session_state.quick_search_results = agent.deps.quick_search_results
    

def process_query_sync(query: str):
    """Synchronous wrapper for async process_query"""
    if not st.session_state.loop.is_running():
        return st.session_state.loop.run_until_complete(process_query(query))
    else:
        # Create a new event loop if the current one is running
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(process_query(query))
        finally:
            loop.close()

def reset_chat():
    """Reset the chat history and agent state."""
    agent.reset()
    st.session_state.chat_history = []
    st.session_state.research_paper = {}
    st.session_state.table_data = {}
    st.session_state.quick_search_results = []
    st.session_state.agent_memory = []
    


# Streamlit UI
st.title("Research Assistant Chatbot")

# Create a container for the chat interface
chat_container = st.container()

# Create two columns - one for chat and one for controls



# Chat interface with custom styling
st.markdown("""
    <style>
    .stChatMessage {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .user-message {
        background-color: #e6f3ff;
        text-align: right;
    }
    .assistant-message {
        background-color: #f0f0f0;
        text-align: left;
    }
    </style>
""", unsafe_allow_html=True)

# Chat messages in a scrollable container
with st.container(height=300):
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🤖"):
            st.write(message["content"])

# Input area at the bottom
with st.container():
    query = st.text_input("Ask me anything...", key="query_input", placeholder="Type your question here...")
    col3, col4 = st.columns([6, 1])
    with col3:
        if st.button("Submit", use_container_width=True):
            if query:
                with st.spinner('Processing your request...'):
                    process_query_sync(query)
                    st.rerun()


# Control buttons in the sidebar
with st.sidebar:
    st.markdown("### Helpful Tips")
    st.markdown("---")
    st.markdown("""reset chat if you want to start over or if the agent is not responding properly""")
    if st.button("Reset Chat", use_container_width=True):
        reset_chat()

    # Add some helpful tips
    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("""
    - ask the agent about its capabilities and what it can do
    - the table is editable, you can edit in the files section or in the chat
    - the research paper is also editable, you can edit in the chat by asking the agent to edit the research paper
    - the agent can also add a table to the research paper, you can see the table in the files section or in the chat
    """)

st.markdown('### Files ')

# Research Paper popover
 
if st.session_state.research_paper :
    with st.popover("📄 Research Paper",use_container_width=True):
        st.markdown("""
        <style>
        .paper-preview {
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Paper content
        st.markdown(paper_to_markdown(st.session_state.research_paper))
        
        # Download button
        if st.button("📥 Save as DOCX", use_container_width=True):
            with st.spinner('Preparing document...'):
                output_path = download_as_docx(st.session_state.research_paper)
                with open(output_path, "rb") as file:
                    st.download_button(
                        label="Download",
                        data=file,
                        file_name="research_paper.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                os.unlink(output_path)

# Table popover
if st.session_state.table_data:
    with st.popover("📊 Editable Table",use_container_width=True):
        try:
            try:
                df = pd.DataFrame(data=st.session_state.table_data['data'], 
                                columns=st.session_state.table_data['columns'])
            except:
                df = pd.DataFrame(st.session_state.table_data)
            

            edited_df = st.data_editor(df)
            if st.session_state.research_paper:
                if st.button("💾 add table to research paper", use_container_width=True):
                    # Convert DataFrame back to the correct structure
                    table_dict = {
                        'data': edited_df.values.tolist(),
                        'columns': edited_df.columns.tolist()
                    }
                    st.session_state.research_paper['table'] = table_dict
                    st.session_state.table_data = table_dict
                    st.success("Table updated successfully!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error loading table data: {str(e)}")


