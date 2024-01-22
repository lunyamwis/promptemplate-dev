from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .tasks import scrap_instagram
# Create your views here.

class InstagramScrapper(APIView):
    def post(self,request):
        accounts = request.data.get("accounts",[])
        followers = request.data.get("get_followers")
        scrap_instagram(accounts,followers)
        return Response({"success":True},status=status.HTTP_200_OK)