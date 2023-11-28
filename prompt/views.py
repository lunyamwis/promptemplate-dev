import json

from django.shortcuts import render
from django.db import connections
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .models import Prompt, Query
from product.models import Company, Problem, Solution, GsheetSetting
from itertools import chain
from .forms import PromptForm
from helpers.db.connection import connect_to_external_database
from helpers.gsheet.utils import execute_gsheet_formula


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

class GetPrompt(APIView):
    def post(self, request):
        data = request.data
        prompt_index = data.get("prompt_index")
        company_index = data.get("company_index")
        prompt = Prompt.objects.filter(index=int(prompt_index), product__company__index=int(company_index)).last()
        prompt_data =  f"""{prompt.text_data}-{list(chain.from_iterable([prompt.querying_info, 
        prompt.get_problems, prompt.get_solutions] ) )}"""

        return Response({
            "prompt": prompt_data,
            "steps": prompt.product.steps,
        }, status=status.HTTP_200_OK)