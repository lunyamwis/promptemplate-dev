from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render, redirect, get_object_or_404
from product.models import Product, Company
from .models import Prompt, Problem, Solution
from itertools import chain
from .forms import PromptForm


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
        product = Product.objects.get(name=data.get("product_name"), company=company)
        prompt = Prompt.objects.filter(index=int(data.get("prompt_index")), product=product).last()
        prompt.data = data
        prompt.save()
        
        return Response({
            "success":True,
        }, status=status.HTTP_200_OK)

class getPrompt(APIView):
    
    def post(self, request):
        # import pdb;pdb.set_trace()
        data = request.data
        company = Company.objects.get(name=data.get("company_name"))
        product = Product.objects.get(name=data.get("product_name"), company=company)
        prompt = Prompt.objects.filter(index=int(data.get("prompt_index")), product=product).last()
        prompt_data =  f"""
                        {prompt.text_data}-
                        Tone of voice: {prompt.tone_of_voice.description}

                        Problems: {list(Problem.objects.all()) if prompt.index == 2 else ""}
                        Solutions: {list(Solution.objects.all()) if prompt.index == 3 else ""}

                        Confirmed Problems: { prompt.data if prompt.index >= 3 else ""}
                        
                        Conversation so far: {data.get("conversations", "")}
                        More information about the user: {data.get("outsourced", "") if prompt.index == 1 else ""}
                    """
        
        return Response({
            "prompt": prompt_data,
            "steps": prompt.product.steps,
        }, status=status.HTTP_200_OK)