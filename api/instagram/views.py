import yaml
import os
import json
import logging
import requests
import pandas as pd
import subprocess

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404
from .tasks import scrap_followers,scrap_info,scrap_users,insert_and_enrich,scrap_mbo
from api.helpers.dag_generator import generate_dag
from api.helpers.date_helper import datetime_to_cron_expression
from boostedchatScrapper.spiders.helpers.thecut_helper import scrap_the_cut
from django.db.models import Q
from .models import InstagramUser

from rest_framework import viewsets
from boostedchatScrapper.models import ScrappedData
from .models import Score, QualificationAlgorithm, Scheduler, LeadSource,DagModel,SimpleHttpOperatorModel,WorkflowModel
from .serializers import ScoreSerializer, QualificationAlgorithmSerializer, SchedulerSerializer, LeadSourceSerializer, SimpleHttpOperatorModelSerializer, WorkflowModelSerializer

class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer

class QualificationAlgorithmViewSet(viewsets.ModelViewSet):
    queryset = QualificationAlgorithm.objects.all()
    serializer_class = QualificationAlgorithmSerializer

class SchedulerViewSet(viewsets.ModelViewSet):
    queryset = Scheduler.objects.all()
    serializer_class = SchedulerSerializer

class LeadSourceViewSet(viewsets.ModelViewSet):
    queryset = LeadSource.objects.all()
    serializer_class = LeadSourceSerializer


class SimpleHttpOperatorViewSet(viewsets.ModelViewSet):
    queryset = SimpleHttpOperatorModel.objects.all()
    serializer_class = SimpleHttpOperatorModelSerializer

class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = WorkflowModel.objects.all()
    serializer_class = WorkflowModelSerializer

    
class ScrapFollowers(APIView):
    def post(self, request):
        username = request.data.get("username")
        delay = int(request.data.get("delay"))
        round_ =  int(request.data.get("round"))
        chain = request.data.get("chain")
        if isinstance(username,list):
            for account in username:
                if chain:
                    scrap_followers(account,delay,round_=round_)
                else:
                    scrap_followers.delay(account,delay,round_=round_)
        else:
            scrap_followers.delay(username,delay,round_=round_)
        return Response({"success":True},status=status.HTTP_200_OK)

class ScrapTheCut(APIView):

    def post(self,request):
        chain = request.data.get("chain")
        round_ = request.data.get("round")
        index = request.data.get("index")
        try:
            scrap_the_cut(round_number=round_)
            users = ScrappedData.objects.filter(round_number=round_)
            if users.exists():
                if chain:
                    for user in users:
                        scrap_users(list(user.response.get("keywords")[1]),round_ = round_,index=index)
                else:
                    for user in users:
                        scrap_users.delay(list(user.response.get("keywords")[1]),round_ = round_,index=index)

                return Response({"success": True}, status=status.HTTP_200_OK)
            else:
                logging.warning("Unable to find user")
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScrapStyleseat(APIView):

    def post(self,request):
        region = request.data.get("region")
        category = request.data.get("category")
        chain = request.data.get("chain")
        round_ = request.data.get("round")
        index = request.data.get("index")
        try:
            subprocess.run(["scrapy", "crawl", "styleseat","-a",f"region={region}","-a",f"category={category}"])
            users = ScrappedData.objects.filter(inference_key=region)
            if users.exists():
                if chain:
                    for user in users:
                        scrap_users(list(user.response.get("businessName")),round_ = round_,index=index)
                else:
                    for user in users:
                        scrap_users.delay(list(user.response.get("businessName")),round_ = round_,index=index)

                return Response({"success": True}, status=status.HTTP_200_OK)
            else:
                logging.warning("Unable to find user")
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScrapGmaps(APIView):

    def post(self,request):
        search_string = request.data.get("search_string")
        chain = request.data.get("chain")
        round_ = request.data.get("round")
        index = request.data.get("index")
        try:
            subprocess.run(["scrapy", "crawl", "gmaps","-a",f"search_string={search_string}"])
            users = ScrappedData.objects.filter(inference_key=search_string)
            if users.exists():
                if chain:
                    for user in users:
                        scrap_users(list(user.response.get("business_name")),round_ = round_,index=index)
                else:
                    for user in users:
                        scrap_users.delay(list(user.response.get("business_name")),round_ = round_,index=index)

                return Response({"success": True}, status=status.HTTP_200_OK)
            else:
                logging.warning("Unable to find user")
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class ScrapAPI(APIView):

    def get(self,request):
        try:
            # Execute Scrapy spider using the command line
            subprocess.run(["scrapy", "crawl", "api"])
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


class ScrapSitemaps(APIView):

    def get(self,request):
        try:
            # Execute Scrapy spider using the command line
            subprocess.run(["scrapy", "crawl", "sitemaps"])
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class ScrapMindBodyOnline(APIView):

    def post(self,request):
        chain = request.data.get("chain")
        try:
            if chain:
                scrap_mbo()
            else:    
                # Execute Scrapy spider using the command line
                scrap_mbo.delay()
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScrapURL(APIView):

    def get(self,request):
        try:
            # Execute Scrapy spider using the command line
            subprocess.run(["scrapy", "crawl", "webcrawler"])
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ScrapUsers(APIView):
    def post(self,request):
        query = request.data.get("query")
        round_ = int(request.data.get("round"))
        index = int(request.data.get("index"))
        chain = request.data.get("chain")

        if isinstance(query,list):
            if chain:
                scrap_users(query,round_ = round_,index=index)
            else:
                scrap_users.delay(query,round_ = round_,index=index)
            
        return Response({"success":True},status=status.HTTP_200_OK)

class ScrapInfo(APIView):
    def post(self,request):
        delay_before_requests = int(request.data.get("delay_before_requests"))
        delay_after_requests = int(request.data.get("delay_after_requests"))
        step = int(request.data.get("step"))
        accounts = int(request.data.get("accounts"))
        round_number = int(request.data.get("round"))
        chain = request.data.get("chain")
        if chain:
            scrap_info(delay_before_requests,delay_after_requests,step,accounts,round_number)
        else:
            scrap_info.delay(delay_before_requests,delay_after_requests,step,accounts,round_number)
        return Response({"success":True},status=status.HTTP_200_OK)
    



class InsertAndEnrich(APIView):
    def post(self,request):
        keywords_to_check = request.data.get("keywords_to_check")
        round_ = request.data.get("round")
        chain = request.data.get("chain")
        if chain:
            insert_and_enrich(keywords_to_check,round_)
        else:
            insert_and_enrich.delay(keywords_to_check,round_)
        return Response({"success":True},status=status.HTTP_200_OK)
    

class GetMediaIds(APIView):
    def post(self,request):
        round_ = request.data.get("round")
        chain = request.data.get("chain")
        
        datasets = []
        for user in InstagramUser.objects.filter(Q(round=round_) & Q(qualified=True)):
            resp = requests.post(f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com/v1/instagram/has-client-responded/",data={"username":user.username})
            print(resp.status_code)
            if resp.status_code == 200:
                if resp.json()['has_responded']:
                    return Response({"message":"No need to carry on further because client has responded"}, status=status.HTTP_200_OK)
            else:
                resp = requests.get(f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com/v1/instagram/account/retrieve-salesrep/{user.username}/")
                if resp.status_code == 200:
                    print(resp.json())
                    dataset = {
                        "mediaIds": user.info.get("media_id"),
                        "username_from": resp.json()['salesrep'].get('username','')
                    }
                    datasets.append(dataset)
            

        if chain and round_:  
            return Response({"data": datasets},status=status.HTTP_200_OK)
        else:
            return Response({"error":"There is an error fetching medias"}, status=400)
        

class GetMediaComments(APIView):
    def post(self,request):
        round_ = request.data.get("round")
        chain = request.data.get("chain")
        
        datasets = []
        for user in InstagramUser.objects.filter(Q(round=round_) & Q(qualified=True)):
            resp = requests.post(f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com/v1/instagram/has-client-responded/",data={"username":user.username})
            print(resp.status_code)
            if resp.status_code == 200:
                if resp.json()['has_responded']:
                    return Response({"message":"No need to carry on further because client has responded"}, status=status.HTTP_200_OK)
            else:
                resp = requests.get(f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com/v1/instagram/account/retrieve-salesrep/{user.username}/")
                if resp.status_code == 200:
                    print(resp.json())
                    dataset = {
                        "mediaId": user.info.get("media_id"),
                        "comment": user.info.get("media_comment"),
                        "username_from": resp.json()['salesrep'].get('username','')
                    }
                    datasets.append(dataset)

        
        
        if chain and round_:  
            return Response({"data": datasets},status=status.HTTP_200_OK)
        else:
            return Response({"error":"There is an error fetching medias"}, status=400)
        
class GetAccounts(APIView):
    def post(self,request):
        round_ = request.data.get("round")
        chain = request.data.get("chain")
        
        datasets = []
        for user in InstagramUser.objects.filter(Q(round=round_) & Q(qualified=True)):
            resp = requests.post(f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com/v1/instagram/has-client-responded/",data={"username":user.username})
            print(resp.status_code)
            if resp.status_code == 200:
                if resp.json()['has_responded']:
                    return Response({"message":"No need to carry on further because client has responded"}, status=status.HTTP_200_OK)
            else:
                resp = requests.get(f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com/v1/instagram/account/retrieve-salesrep/{user.username}/")
                if resp.status_code == 200:
                    print(resp.json())
                    dataset = {
                        "usernames_to": user.info.get("username"),
                        "username_from": resp.json()['salesrep'].get('username','')
                    }
                    datasets.append(dataset)
        
        
        if chain and round_:  
            return Response({"data": datasets},status=status.HTTP_200_OK)
        else:
            return Response({"error":"There is an error fetching medias"}, status=400)
        
