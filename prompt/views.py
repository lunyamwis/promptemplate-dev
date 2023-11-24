import json

from django.shortcuts import render
from django.db import connections
# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .models import Prompt, Query
from product.models import Company, Problem, Solution
from .forms import PromptForm
from helpers.db.connection import connect_to_external_database
from helpers.gsheet.utils import get_range


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
    prompt = get_object_or_404(Prompt,id = prompt_id)
    querying_info = []
    queries = Query.objects.filter(prompt = prompt)

    # getting queries
    for query_ in queries:
        company = get_object_or_404(Company, id = prompt.product.company.id)
        connect_to_external_database(company)
        with connections[company.name].cursor() as cursor:
            cursor.execute(query_.query)
            results = cursor.fetchall()
        
        query_data = {
            query_.name:results if results else query_.query
        }
        querying_info.append(query_data)
    

    # getting gsheet info
    
    return render(request, 'prompt/detail.html', {
                'prompt': prompt,
                'query_info':querying_info
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
