import os
import openai
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
import requests
from pydantic import BaseModel, Field
from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import MessagesPlaceholder
import datetime
import wikipedia
from langchain_openai.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import DocArrayInMemorySearch
from langchain.schema.runnable import RunnableMap
from langchain.memory import ConversationBufferMemory
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents import AgentExecutor
import panel as pn  # GUI
import param

# Load environment variables
_ = load_dotenv(find_dotenv())  # read local .env file

# Define tools
class OpenMeteoInput(BaseModel):
    latitude: float = Field(..., description="Latitude of the location to fetch weather data for")
    longitude: float = Field(..., description="Longitude of the location to fetch weather data for")

@tool(args_schema=OpenMeteoInput)
def get_current_temperature(latitude: float, longitude: float) -> dict:
    """Fetch current temperature for given coordinates."""
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': 'temperature_2m',
        'forecast_days': 1,
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        results = response.json()
    else:
        raise Exception(f"API Request failed with status code: {response.status_code}")

    current_utc_time = datetime.datetime.utcnow()
    time_list = [datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00')) for time_str in results['hourly']['time']]
    temperature_list = results['hourly']['temperature_2m']
    closest_time_index = min(range(len(time_list)), key=lambda i: abs(time_list[i] - current_utc_time))
    current_temperature = temperature_list[closest_time_index]
    return f'The current temperature is {current_temperature}°C'

@tool
def search_wikipedia(query: str) -> str:
    """Run Wikipedia search and get page summaries."""
    page_titles = wikipedia.search(query)
    summaries = []
    for page_title in page_titles[:3]:
        try:
            wiki_page = wikipedia.page(title=page_title, auto_suggest=False)
            summaries.append(f"Page: {page_title}\nSummary: {wiki_page.summary}")
        except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
            pass
    if not summaries:
        return "No good Wikipedia Search Result was found"
    return "\n\n".join(summaries)

@tool
def create_your_own(query: str) -> str:
    """This function can do whatever you would like once you fill it in."""
    return query[::-1]

@tool
def rapport_building(query: str) -> str:
    """This function furnishes the user with rapport building data."""
    pass

# Vector store and retriever setup
vectorstore = DocArrayInMemorySearch.from_texts(
    ["..."],  # Add your prompt texts here
    embedding=OpenAIEmbeddings()
)
retriever = vectorstore.as_retriever()
tools = [get_current_temperature, search_wikipedia, create_your_own]
functions = [convert_to_openai_function(f) for f in tools]
model = ChatOpenAI(temperature=0).bind(functions=functions)

# GUI with Panel
pn.extension()

class cbfs(param.Parameterized):
    
    def __init__(self, tools, retriever, **params):
        super(cbfs, self).__init__(**params)
        self.panels = []
        self.tools_ = [get_current_temperature, search_wikipedia, create_your_own]
        self.vectorstore = DocArrayInMemorySearch.from_texts(
            ["""
            Aim
            1st: connect, show appreciation for the identity they manifest and industry expertise, and ask how long in the business. 2nd: lead the live conversation to understand if serving existing clients or attracting new ones is more important for their business. 

            Message Construction Rules:
            The response must be constructed as a single, concise message using simple sentence structures encapsulated within one JSON entry ("text").
            Personalize, use one question per message to engage and steer the conversation toward my aim. Unless the name is evident in information about the respondent or conversation history skip it, otherwise occasionally use an informal name that a friend would use.

            Conditional Responses and Statuses:
            - No Previous Conversation:  Impressed by their craft aesthetics establish a connection, ask how long they're in the business and introduce myself.
            - Last Message from Respondent: Switch to "completed": "1" only if my response directly asks the question in 2nd part of aim stated above.
            - The respondent is unhappy with their current booking system, or client acquisition, or is considering switching to Booksy: switch "status": "high_potential"
            - Assign "script_score" from 0 to 50: 0 for disinterest, up to 25 for engagement, 26-40 for business insights, and 41-50 for clear interest in solutions.  
            - Respondent doubts they're talking to human: switch “human_takeover”: “1".
            - Last message from me: Craft a message that gently re-engages the respondent, steering the conversation towards my aim. The message should be open-ended, inviting a response.

            JSON Output Structure:
            {"text": "message", "completed": "0" or "1", "status": "unknown" or "high_potential",  "script_score": "number between 0 and 50 based on engagement criteria", “human_takeover”: “0” or “1", "script_version": "1.2"}
            """, 
            """
            Aim:
            Engage with the respondent to understand which 2 potential problems from the provided list they're facing, and the problem's business impact. Emphatically confirm that I understand what they're going through and that I've seen a lot of people facing those and have supportive insights.

            Message Construction Rules
            - Write as short as possible Instagram Direct Message according to my Aim in response to the most recent conversation history.
            - Lead towards potential problems by asking only 1 question per message [open-ended first (e.g. the good, bad & ugly of your booking system), closed-ended when confirming the problem]
            - When the Respondent's last message mentions a new problem, empathically prove that I understand them, have seen others struggle with it, and learn how it impacts their business (e.g. reengaging 1 inactive client increases their revenue by $600+ annually)
            - directly address conversation_history or the problems lists.
            - Prioritize in-depth discussion of potential problems mentioned but not yet confirmed.
            - Except for understanding business impact, avoid revisiting problems already confirmed in the conversation. Focus on unresolved or new potential issues."
            - Unless the name is evident in information about the respondent or conversation history skip it, otherwise occasionally use an informal name that a friend would use.
            - If a problem is Booksy-related, act surprised and plan to research more as people usually love it, don't confirm the problem.
            - Respond in JSON format only, without any introductory or concluding remarks.

            Conditional Responses and Statuses
            - Confirmed Problem: Acknowledge and empathize with each problem confirmed from the conversation history, listed under 'Problem'. Avoid repeating questions about these problems. Record confirmed problems in the JSON array 'confirmed_problems' with the format: ++confirmed problem - [item from Problem list]++. 
            - Rejected Problem: ++rejected problem - [rejected problem from the problem list]++
            - Last message from me: Craft a message that gently re-engages the respondent, steering the conversation towards my aim. The message should be open-ended, inviting a response.
            - Respondent doubts they're talking to human: switch “human_takeover”: “1".
            - Assign "script_score" from 0 to 75: 0 for disinterest, 50-75 when confirming important problems.  
            - Completion Criteria: After a problem is confirmed, increment the count of confirmed problems. Once the count reaches two, immediately update the "completed" status in the JSON output to "1". If fewer than two problems are confirmed, maintain the "completed" status as "0".

            JSON Output Structure:
            {
            "text": "crafted_message", 
            "completed": "0" or “1” (set to "1" immediately after the second problem is confirmed),
            “confirmed_problems”: ”list of confirmed problems”, "script_score": "number between 0 and 75 based on engagement criteria",
            “human_takeover”: “0” or “1", "script_version": "2.0"
            }
            """
            ],
            embedding=OpenAIEmbeddings()
        )
        
        self.retriever = self.vectorstore.as_retriever()
        self.functions = [convert_to_openai_function(f) for f in tools]
        self.model = ChatOpenAI(temperature=0).bind(functions=self.functions)
        self.memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
        self.chain = None
        self.qa = None
        self.init_chain()

    def init_chain(self):
        # Initialize the chain with a default prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful but sassy assistant"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        self.chain = RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_functions(x["intermediate_steps"])
        ) | self.prompt | self.model | OpenAIFunctionsAgentOutputParser()
        self.qa = AgentExecutor(agent=self.chain, tools=self.tools_, verbose=False, memory=self.memory)

    def update_prompt(self, query):
        relevant_docs = self.retriever.get_relevant_documents(query)
        if relevant_docs:
            relevant_content = relevant_docs[0].page_content
            print(relevant_content)
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", f"{relevant_content}"),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            self.init_chain()

    def convchain(self, query):
        if not query:
            return
        inp.value = ''
        self.update_prompt(query)
        result = self.qa.invoke({"input": query})
        
        self.answer = result['output'] 
        self.panels.extend([
            pn.Row('User:', pn.pane.Markdown(query, width=450)),
            pn.Row('ChatBot:', pn.pane.Markdown(self.answer, width=450, styles={'background-color': '#F6F6F6'}))
        ])
        return pn.WidgetBox(*self.panels, scroll=True)

    def clr_history(self):
        self.memory.clear()
        self.panels = []
        return 


cb = cbfs(tools, retriever)

inp = pn.widgets.TextInput(placeholder='Enter text here…')

conversation = pn.bind(cb.convchain, inp) 

tab1 = pn.Column(
    pn.Row(inp),
    pn.layout.Divider(),
    pn.panel(conversation, loading_indicator=True, height=400),
    pn.layout.Divider(),
)

dashboard = pn.Column(
    pn.Row(pn.pane.Markdown('# QnA_Bot')),
    pn.Tabs(('Conversation', tab1))
)
dashboard.show(port=4355)

