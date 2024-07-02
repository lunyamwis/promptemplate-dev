import json
from django.shortcuts import render
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import redirect, get_object_or_404
from product.models import Product, Company
from prompt.serializers import CreatePromptSerializer, CreateRoleSerializer, PromptSerializer, RoleSerializer
from .factory import PromptFactory
from .models import Prompt, Role, ChatHistory
from .forms import PromptForm
import os
import openai
import base64
import random
import uuid
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
import requests
import re
from pydantic import BaseModel, Field
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain.prompts import MessagesPlaceholder
import datetime
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
from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
from crewai_tools import DirectoryReadTool, FileReadTool, SerperDevTool,BaseTool
from crewai import Agent, Task, Crew
from django.core.mail import send_mail
from .models import Agent as AgentModel,Task as TaskModel,Tool, Department
import os
from typing import List,Optional

openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ["OPENAI_MODEL_NAME"] = 'gpt-4-1106-preview'
os.environ["SERPER_API_KEY"] = os.getenv('SERPER_API_KEY')


def index(request):
    prompts = Prompt.objects.all()
    return render(request, 'prompt/index.html', {'prompts': prompts})


def add(request):
    if request.method == 'POST':
        form = PromptForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = PromptForm()
    return render(request, 'prompt/add.html', {'form': form})


def detail(request, prompt_id):
    prompt = get_object_or_404(Prompt, id=prompt_id)

    return render(request, 'prompt/detail.html', {
        'prompt': prompt,
    })


def update(request, prompt_id):
    prompt = get_object_or_404(Prompt, pk=prompt_id)
    if request.method == 'POST':
        form = PromptForm(request.POST, instance=prompt)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = PromptForm(instance=prompt)
    return render(request, 'prompt/update.html', {'form': form, 'prompt': prompt})


def delete(request, prompt_id):
    prompt = get_object_or_404(Prompt, pk=prompt_id)
    prompt.delete()
    return redirect('index')


class saveResponse(APIView):

    def post(self, request):
        data = request.data
        company = Company.objects.get(name=data.get("company_name"))
        product = Product.objects.get(
            name=data.get("product_name"), company=company)
        prompt = Prompt.objects.filter(
            index=int(data.get("prompt_index")) + 1, product=product).last()
        prompt.data = data
        prompt.save()

        return Response({
            "success": True,
        }, status=status.HTTP_200_OK)

def retrieve_prompt(userInput):
    resp = requests.get("https://promptemplate.booksy.us.boostedchat.com/prompts/")
    prompts = [prompt['text_data'] for prompt in resp.json()]
    character_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", " ", ""],
        chunk_size=1000,
        chunk_overlap=0
    )
    character_split_texts = character_splitter.split_text('\n\n'.join(prompts))
    token_splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=0, tokens_per_chunk=256)

    token_split_texts = []
    for text in character_split_texts:
        token_split_texts += token_splitter.split_text(text)

    embedding_function = SentenceTransformerEmbeddingFunction()
    chroma_client = chromadb.Client()
    chroma_collection = chroma_client.create_collection(f"prompts-{random.randint(1,1000)}", embedding_function=embedding_function)

    ids = [str(i) for i in range(len(token_split_texts))]

    chroma_collection.add(ids=ids, documents=token_split_texts)
    chroma_collection.count()
    results = chroma_collection.query(query_texts=[userInput], n_results=5)
    retrieved_documents = results['documents'][0]
    return retrieved_documents

def model_with_extra_info(data):
    template = """Answer the user based only on the following context and information and remember to conceal your identity as a robot, you are a sales representative:
            {context}
        information: {information}
        userInput: {userInput}
        """
    prompt = ChatPromptTemplate.from_template(template)
    model = ChatOpenAI(temperature=0)
    output_parser = StrOutputParser()
    chain = RunnableMap({
        "context": lambda x: retrieve_prompt(x["userInput"]),
        "userInput": lambda x: x["userInput"],
        "information": lambda x: x["information"]
    }) | prompt | model | output_parser
    result = chain.invoke(data)
    get_prompt = RunnableMap({
        "context": lambda x: retrieve_prompt(x["userInput"]),
        "userInput": lambda x: x["userInput"],
        "information": lambda x: x["information"]
    }) | prompt
    return {
        "result":result,
        "prompt":get_prompt.invoke(data),
        "model":model
    }

import string

def remove_punctuation(sentence):
    punctuation_to_keep = {'.', ',', '\''}
    punctuation_to_remove = ''.join(p for p in string.punctuation if p not in punctuation_to_keep) + '{}[]'
    table = str.maketrans('', '', punctuation_to_remove)
    return sentence.translate(table)

import sqlite3

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('conversation_history.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY,
        role TEXT NOT NULL,
        content TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

init_db()
def save_message(role, content):
    conn = sqlite3.connect('conversation_history.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chat_history (role, content) VALUES (?, ?)', (role, content))
    conn.commit()
    conn.close()

def load_messages():
    conn = sqlite3.connect('conversation_history.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role, content FROM chat_history')
    messages = cursor.fetchall()
    conn.close()
    return messages

@tool
def get_sales_representative_data(userInput):
    """this function returns the sales representative data and information about their role"""
    resp = requests.get("https://promptemplate.booksy.us.boostedchat.com/roles/-NmvqgR8ySgPtYKXiQ1c/")
    result = model_with_extra_info({"userInput":userInput,"information":resp.json()['description']})
    return result['result']

class generateResponse(APIView):
    def post(self, request):
        userInput = request.data.get("userInput")
        username_from_id = request.data.get("username_from_id","")
        username_to_id = request.data.get("username_to_id","")
        tools = [get_sales_representative_data]
        functions = [convert_to_openai_function(f) for f in tools]
        # model_with_extra_info = ChatOpenAI(temperature=0).bind(functions=functions)
        
        # Load existing conversation history
        chat_history = ChatHistory.objects.filter(Q(username_from_id=username_from_id)&Q(username_to_id=username_to_id))
        print(chat_history)
        
        # Initialize memory
        memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")

        # Add loaded messages to memory
        for chat in chat_history:
            if chat.role == 'user':
                memory.chat_memory.add_user_message(chat.content)
            elif chat.role == 'assistant':
                memory.chat_memory.add_ai_message(chat.content)

        # Construct the initial result with extra information
        result = model_with_extra_info({"userInput": userInput, "information": "Conceal your identity as a robot, you are a sales representative"})
        print(result)
        
        final_prompt = ChatPromptTemplate.from_messages([
            ("system", remove_punctuation(result['prompt'].messages[0].content)),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{userInput}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Create the chain
        model = ChatOpenAI(temperature=0).bind(functions=functions)
        
        chain = RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_functions(x["intermediate_steps"])
        ) | final_prompt | model | OpenAIFunctionsAgentOutputParser()
        
        # Create the agent executor with memory integration
        qa = AgentExecutor(agent=chain, tools=tools, verbose=False, memory=memory)
        
        # Invoke the chain and get the response
        response = qa.invoke({"userInput": userInput})
        
        # Save user input and AI response to SQLite
        ChatHistory.objects.create(role='user', content=userInput,username_from_id=username_from_id,username_to_id=username_to_id)
        ChatHistory.objects.create(role='assistant',content= response['output'],username_from_id=username_from_id,username_to_id=username_to_id)
        
        # Save the updated memory context
        memory.save_context({"input": userInput}, {"output": response['output']})
        
        return Response({
            "response": response
        }, status=status.HTTP_200_OK)


class SentimentAnalysisTool(BaseTool):
    name: str ="Sentiment Analysis Tool"
    description: str = ("Analyzes the sentiment of text "
         "to ensure positive and engaging communication.")
    
    def _run(self, text: str) -> str:
        # Your custom code tool goes here
        return "positive"
    

class ScrappingTheCutTool(BaseTool):
    name: str = "scrapping_thecut_tool"
    description: str = """Allows one to be able to scrap from the cut effectively either,
                        per single or multiple records"""
    # number_of_leads: Optional[str] = None
    endpoint: str = "https://e405-35-189-218-230.ngrok-free.app/instagram/scrapTheCut/"


    def _run(self,number_of_leads):
        # import pdb;pdb.set_trace()
        headers = {"Content-Type": "application/json"}
        payload = {
            "chain":True,
            "round":134,
            "index":0,
            "record":None,
            "refresh":False,
            "number_of_leads":number_of_leads
        }
        # import pdb;pdb.set_trace()
        response = requests.post(self.endpoint, data=json.dumps(payload), headers=headers)
        return response.json()

class InstagramSearchingUserTool(BaseTool):
    name: str = "search_instagram_tool"
    description: str = """Allows one to be able to scrap from instagram effectively either,
                        per single or multiple records"""
    # number_of_leads: Optional[str] = None
    endpoint: str = "https://e405-35-189-218-230.ngrok-free.app/instagram/scrapUsers/"

    def _run(self,**kwargs):
        # import pdb;pdb.set_trace()
        headers = {"Content-Type": "application/json"}
        payload = {
            "chain":True,
            "round":134,
            "index":0,
            "query":None
        }
        # import pdb;pdb.set_trace()
        response = requests.post(self.endpoint, data=json.dumps(payload), headers=headers)
        return response.json()

class InstagramScrapingProfileTool(BaseTool):
    name: str = "scrapping_instagram_profile_tool"
    description: str = """Allows one to be able to scrap from instagram effectively either,
                        per single or multiple records"""
    # number_of_leads: Optional[str] = None
    endpoint: str = "https://e405-35-189-218-230.ngrok-free.app/instagram/scrapInfo/"

    def _run(self,**kwargs):
        # import pdb;pdb.set_trace()
        headers = {"Content-Type": "application/json"}
        payload = {
            "chain":True,
            "round":134,
            "index":0,
            "delay_before_requests":18,
            "delay_after_requests":4,
            "step":3,
            "accounts":18,
        }
        # import pdb;pdb.set_trace()
        response = requests.post(self.endpoint, data=json.dumps(payload), headers=headers)
        return response.json()

class LeadScreeningTool(BaseTool):
    name: str = "fetch_leads"
    description: str = """Allows one to be able to fetch sorted leads that meet certain
                        criterion"""
    # number_of_leads: Optional[str] = None
    endpoint: str = "https://e405-35-189-218-230.ngrok-free.app/instagram/getAccounts/"

    def _run(self,**kwargs):
        # import pdb;pdb.set_trace()
        headers = {"Content-Type": "application/json"}
        payload = {
            "chain":True,
            "round":134
        }
        # import pdb;pdb.set_trace()
        response = requests.post(self.endpoint, data=json.dumps(payload), headers=headers)
        return response.json()

class FetchLeadTool(BaseTool):
    name: str = "fetch_lead"
    description: str = """Allows one to be able to fetch a lead that meet certain
                        criterion"""
    # number_of_leads: Optional[str] = None
    endpoint: str = "https://e405-35-189-218-230.ngrok-free.app/instagram/getAccount/"

    def _run(self,**kwargs):
        # import pdb;pdb.set_trace()
        headers = {"Content-Type": "application/json"}
        payload = {
            "chain":True,
            "round":134
        }
        # import pdb;pdb.set_trace()
        response = requests.post(self.endpoint, data=json.dumps(payload), headers=headers)
        return response.json()


class SlackTool(BaseTool):
    name: str = "slack_tool"
    description: str = """This tool triggers slacks message"""

    def _run(self, message, **kwargs):
        # send the message to the following email -- chat-quality-aaaamvba2tskkthmspu2nrq5bu@boostedchat.slack.com
        send_mail(subject="Scrapping Monitoring Agent Summary",message=message,from_email="lutherlunyamwi@gmail.com",recipient_list=["chat-quality-aaaamvba2tskkthmspu2nrq5bu@boostedchat.slack.com"])
        return "sent message"

class AssignSalesRepTool(BaseTool):
    name: str = "assign_sales_rep_tool"
    description: str = """This tool will assign a lead to a salesrepresentative"""

    endpoint: str = "https://9ccf-2c0f-2a80-10e3-6910-17d0-37c3-e0d3-185a.ngrok-free.app/v1/sales/rep/assign-salesrep"

    def _run(self,username, **kwargs):
        # import pdb;pdb.set_trace()
        headers = {"Content-Type": "application/json"}
        payload = {"username":username}
        # import pdb;pdb.set_trace()
        response = requests.post(self.endpoint, data=json.dumps(payload), headers=headers)
        return response.json()


class AssignInfluencerTool(BaseTool):
    name: str = "assign_influencer_tool"
    description: str = """This tool will assign a lead to an influencer"""

    endpoint: str = "https://9ccf-2c0f-2a80-10e3-6910-17d0-37c3-e0d3-185a.ngrok-free.app/v1/sales/rep/assign-influencer"

    def _run(self,username,**kwargs):
        # import pdb;pdb.set_trace()
        headers = {"Content-Type": "application/json"}
        payload = {"username":username}
        # import pdb;pdb.set_trace()
        response = requests.post(self.endpoint, data=json.dumps(payload), headers=headers)
        return response.json()

class FetchDirectPendingInboxTool(BaseTool):
    name: str = "fetch_pending_inbox_tool"
    description: str = ("Allows fetching of inbox pending requests in instagram")
    endpoint: str = "https://fd8d-2c0f-2a80-10e1-4210-817-bada-7f30-a73c.ngrok-free.app"

    def extract_inbox_data(self, data):
        inbox = data.get('inbox', {})
        threads = inbox.get('threads', [])

        result = []

        for thread in threads:
            users = thread.get('users', [])
            for user in users:
                username = user.get('username')
                thread_id = thread.get('thread_id')
                items = thread.get('items', [])

                for item in items:
                    item_id = item.get('item_id')
                    user_id = item.get('user_id')
                    item_type = item.get('item_type')
                    timestamp = item.get('timestamp')
                    message = item.get('text')

                    data_dict = {
                        'username': username,
                        'thread_id': thread_id,
                        'item_id': item_id,
                        'user_id': user_id,
                        'item_type': item_type,
                        'timestamp': timestamp
                    }

                    if item_type == 'text':
                        data_dict['message'] = message

                    result.append(data_dict)

        return result


    def _run(self, **kwargs):

        # Set the username for which to fetch the pending inbox
        username = 'blendscrafters'
        
        # Send a POST request to the fetchPendingInbox endpoint
        response = requests.post(f'{self.endpoint}/fetchPendingInbox', json={'username_from': username})
        
        # Check the status code of the response
        if response.status_code == 200:
            # Print the response JSON
            print("all is well")
            print(json.dumps(response.json(), indent=2))
            inbox_data = response.json()
            inbox_dataset = self.extract_inbox_data(inbox_data)
            print(inbox_dataset)
            
        else:
            print(f'Request failed with status code {response.status_code}')
        return response.json()

class ApproveRequestTool(BaseTool):  
    name: str = "approve_request_tol"
    description: str = ("Allows approval of requests from pending requests in instagram")
    endpoint: str = "https://fd8d-2c0f-2a80-10e1-4210-817-bada-7f30-a73c.ngrok-free.app"

    def _run(self, **kwargs):
        # Send a POST request to the approve endpoint
        username = 'blendscrafters'
        thread_id = '340282366841710301244259591739503476453'
        response = requests.post(f'{self.endpoint}/approve', json={'username_from': username,'thread_id':thread_id})
        
        # Check the status code of the response
        if response.status_code == 200:
            print('Request approved')
        else:
            print(f'Request failed with status code {response.status_code}')
        return response.json()

class WorkflowTool(BaseTool):
    name: str = "workflow_tool"
    description: str = ("Allows the composition of workflows "
         "in order to create as many workflows as possible")
    endpoint: str = "https://scrapper.booksy.us.boostedchat.com/instagram/workflows/"

    def _run(self, workflow_data: dict, **kwargs) -> str:
        print('==========here is workflow data==========')
        print(workflow_data)
        print('==========here is workflow data==========')
        """
        Sends a POST request to the specified endpoint with the provided workflow data and API key.
        """
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.endpoint, data=json.dumps(workflow_data), headers=headers)
        print('we are here------------',response)
        if response.status_code not in [200,201]:
            raise ValueError(f"Failed to send workflow data: {response.text}")

        return response.status_code

    
    

TOOLS = {
    "directory_read_tool": DirectoryReadTool(directory='prompt/instructions'),
    "file_read_tool": FileReadTool(),
    "search_internet_tool" : SerperDevTool(),
    "sentiment_analysis_tool" : SentimentAnalysisTool(),
    "workflow_tool" : WorkflowTool(),
    "scrapping_thecut_tool" : ScrappingTheCutTool(),
    "fetch_lead_tool":FetchLeadTool(),
    "lead_screening_tool":LeadScreeningTool(),
    "search_instagram_tool":InstagramSearchingUserTool(),
    "instagram_profile_tool":InstagramScrapingProfileTool(),
    "slack_tool":SlackTool(),
    "assign_salesrep_tool":AssignSalesRepTool(),
    "assign_influencer_tool":AssignInfluencerTool(),
    "fetch_pending_inbox_tool":FetchDirectPendingInboxTool(),
    "approve_requests_tool":ApproveRequestTool(),

}

class agentSetup(APIView):
    def post(self,request):
        # workflow_data = request.data.get("workflow_data")
        workflow = None
        department = Department.objects.filter(name = request.data.get("department")).last()

        info = request.data.get(department.baton.start_key)
        agents = []
        tasks = []
        
        department_agents = None
        if department.agents.filter(name = info['relevant_information']['assigned_engagement_agent']).exists():
            department_agents = department.agents.filter(name = info['relevant_information']['assigned_engagement_agent'])
        else:
            department_agents = department.agents.all()
            
        for agent in department_agents:
            print(agent)
            # import pdb;pdb.set_trace()
            if agent.tools.filter().exists():
                agents.append(Agent(
                    role=agent.role.description if agent.role else department.name,
                    goal=agent.goal,
                    backstory=agent.prompt.last().text_data,
                    tools = [TOOLS.get(tool.name) for tool in agent.tools.all()],
                    allow_delegation=False,
                    verbose=True
                ))
            else:
                agents.append(Agent(
                    role=agent.role.description if agent.role else department.name,
                    goal=agent.goal,
                    backstory=agent.prompt.last().text_data,
                    allow_delegation=False,
                    verbose=True
                ))
            
        tasks = []
        
        for task in department.tasks.filter(agent__name = info['relevant_information']['assigned_engagement_agent']).order_by('index'):
            print(task)
            agent_ = None
            for agent in agents:
                if task.agent.goal == agent.goal:
                    agent_ = agent
            if  agent_:
                if task.tools.filter().exists():
                    tasks.append(Task(
                        description=task.prompt.last().text_data if task.prompt.exists() else "perform agents task",
                        expected_output=task.expected_output,
                        tools=[TOOLS.get(tool.name) for tool in task.tools.all()],
 
                       agent=agent_,
                    ))
                else:
                    tasks.append(Task(
                        description=task.prompt.last().text_data if task.prompt.exists() else "perform agents task",
                        expected_output=task.expected_output,
                        agent=agent_,
                    ))
                
          
        
        crew = Crew(
            agents=agents,
            
            tasks=tasks,
            
            verbose=2,
            memory=True,
            # output_log_file='scrappinglogs.txt'
        )
        
        # if workflow_data:
            # workflow_tool = TOOLS.get("workflow_tool")
            # response = workflow_tool._run(workflow_data)
            # inputs.update({"workflow_data":workflow_data})
        # import pdb;pdb.set_trace()
        
        result = crew.kickoff(inputs=info)

        # import pdb;pdb.set_trace()
        if isinstance(result, dict):
            # results = eval(result)
            if department.baton.end_key in result.keys():
                # import pdb;pdb.set_trace()
                # update qualified info and new properties
                endpoints = department.baton.endpoints.all()

                remainder = None
                for endpoint in endpoints:
                    requests.Request(method=endpoint.method,url=endpoint.url,data=eval(endpoint.data),params=eval(endpoint.params))
                # resp = requests.post("https://scrapper.booksy.us.boostedchat.com/instagram/users/update-info",data={"outsourced_info":result})

                
                # kickstart new workflow
                workflow_data = department.next_department
                resp = requests.post("https://scrapper.booksy.us.boostedchat.com/instagram/workflows/",data=workflow_data)
            return Response({"result":result})
        else:
            workflow_data = department.next_department
            # import pdb;pdb.set_trace()
            headers = {"Content-Type": "application/json"}
            resp = requests.post("https://scrapper.booksy.us.boostedchat.com/instagram/workflows/",data=json.dumps(workflow_data),headers=headers)
            if resp.status_code in [200,201]:
                print(resp.json())
            return Response({"result":result})

# class agentSetup(APIView):
#     def get(self, request):
#         pass


class getPrompt(APIView):

    def post(self, request):
        data = request.data
        company = Company.objects.get(name=data.get("company_name"))
        product = Product.objects.get(
            name=data.get("product_name"), company=company)
        prompt = Prompt.objects.filter(
            index=int(data.get("prompt_index")), product=product).last()
        outsourced_data = json.loads(data.get("outsourced"))
        prompt_info = PromptFactory(
            salesrep=data.get("salesrep", "mike_bsky"),
            outsourced_data=outsourced_data,
            product=product,
            prompt=prompt
        )

        prompt_data = f"""
                        {prompt.text_data}-
                        Role: {get_object_or_404(Role, name=data.get("salesrep","mike_bsky")).name} -
                        {get_object_or_404(Role, name=data.get("salesrep","mike_bsky")).description}
                        Tone Of Voice: get_object_or_404(Role, name=data.get("salesrep","mike_bsky")).tone_of_voice

                        Problems: {prompt_info.get_problems(data) if prompt.index == 2 else ""}

                        Confirmed Problems: { prompt.data.get("confirmed_problems") if prompt.index >= 3 else ""}


                        Solutions: {prompt_info.get_solutions() if prompt.index == 3 else ""}

                        Conversation so far: {data.get("conversations", "")}
                        More information about the user: {data.get("outsourced", "") if prompt.index == 1 else ""}
                    """

        return Response({
            "prompt": prompt_data,
            "steps": prompt.product.steps,
        }, status=status.HTTP_200_OK)


class PromptViewSet(viewsets.ModelViewSet):
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer

    def get_serializer_class(self):
        if self.action == "update":
            return CreatePromptSerializer
        return super().get_serializer_class()


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    def get_serializer_class(self):
        if self.action == "update":
            return CreateRoleSerializer
        return super().get_serializer_class()
