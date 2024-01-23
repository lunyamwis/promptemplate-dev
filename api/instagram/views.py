from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .tasks import scrap_instagram,process_followers_dry
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user

# Create your views here.

class InstagramScrapper(APIView):
    def post(self,request):
        accounts = request.data.get("accounts",[])
        followers = request.data.get("get_followers")
        scrap_instagram.delay(accounts,followers)
        return Response({"success":True},status=status.HTTP_200_OK)


class InstagramMoxieCsv(APIView):
    def post(self, request):
        client = login_user(username='darwinokuku',password='DarwinOkuku1*')
        followers, cursor = client.user_followers_gql_chunk(client.user_id_from_username(request.data.get('username')), max_amount=100,end_cursor=cursor)
        process_followers_dry.delay(client,cursor,request.data.get('username'))
        return Response({"success":True},status=status.HTTP_200_OK)
