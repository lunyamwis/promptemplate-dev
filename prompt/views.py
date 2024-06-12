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
from .models import Agent as AgentModel,Task as TaskModel,Tool, Department
import os
from typing import List

openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'
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

    def _arun(self, workflow_data: dict, **kwargs) -> str:
        """
        Sends an asynchronous POST request to the specified endpoint with the provided workflow data and API key.
        """
        print('==========here is async workflow data==========')
        print(workflow_data)
        print('==========here is async workflow data==========')
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.endpoint, data=json.dumps(workflow_data), headers=headers)
        print('we are here asynchronously------------',response)
        if response.status_code not in [200,201]:
            raise ValueError(f"Failed to send workflow data: {response.text}")
        return response.text
    

TOOLS = {

    "directory_read_tool": DirectoryReadTool(directory='prompt/instructions'),
    "file_read_tool": FileReadTool(),
    "search_tool" : SerperDevTool(),
    "sentiment_analysis_tool" : SentimentAnalysisTool(),
    "workflow_tool" : WorkflowTool()
}

class agentSetup(APIView):
    def post(self,request):
        # workflow_data = request.data.get("workflow_data")
        workflow = None
        department = Department.objects.filter(name = request.data.get("workflow")).last()

        info = request.data.get(department.baton.start_key)
        
        
        for agent in department.agents.all():
            print(agent)
            # import pdb;pdb.set_trace()
            if agent.tools.filter().exists():
                agents.append(Agent(
                    role=agent.role.description,
                    goal=agent.goal,
                    backstory=agent.prompt.last().text_data,
                    tools = [TOOLS.get(tool.name) for tool in agent.tools.all()],
                    allow_delegation=False,
                    verbose=True
                ))
            else:
                agents.append(Agent(
                    role=agent.role.description,
                    goal=agent.goal,
                    backstory=agent.prompt.last().text_data,
                    allow_delegation=False,
                    verbose=True
                ))
            
        tasks = []
        
        for task in department.tasks.all():
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
            memory=True
        )
        
        # if workflow_data:
            # workflow_tool = TOOLS.get("workflow_tool")
            # response = workflow_tool._run(workflow_data)
            # inputs.update({"workflow_data":workflow_data})
        # import pdb;pdb.set_trace()

        result = crew.kickoff(inputs={department.baton.start_key:info})
        results = eval(result)
        if department.baton.end_key in results.keys():
            # import pdb;pdb.set_trace()
            # update qualified info and new properties
            endpoints = department.baton.endpoints.all()

            remainder = None
            for endpoint in endpoints:
                requests.Request(method=endpoint.method,url=endpoint.url,data=eval(endpoint.data),params=eval(endpoint.params))
            # resp = requests.post("https://scrapper.booksy.us.boostedchat.com/instagram/users/update-info",data={"outsourced_info":results})

            
            # kickstart new workflow
            workflow_data = department.next_department
            resp = requests.post("https://scrapper.booksy.us.boostedchat.com/instagram/workflows/",data=workflow_data)
        return Response({"result":result})

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
