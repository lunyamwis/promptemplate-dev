import json
from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import redirect, get_object_or_404
from product.models import Product, Company
from prompt.serializers import CreatePromptSerializer, CreateRoleSerializer, PromptSerializer, RoleSerializer
from .factory import PromptFactory
from .models import Prompt, Role
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
        tools = [get_sales_representative_data]
        functions = [convert_to_openai_function(f) for f in tools]
        # model_with_extra_info = ChatOpenAI(temperature=0).bind(functions=functions)
        
        # Load existing conversation history
        chat_history = load_messages()
        print(chat_history)
        
        # Initialize memory
        memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")

        # Add loaded messages to memory
        for role, content in chat_history:
            if role == 'user':
                memory.chat_memory.add_user_message(content)
            elif role == 'assistant':
                memory.chat_memory.add_ai_message(content)

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
        save_message('user', userInput)
        save_message('assistant', response['output'])
        
        # Save the updated memory context
        memory.save_context({"input": userInput}, {"output": response['output']})
        
        return Response({
            "response": response
        }, status=status.HTTP_200_OK)

    



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
