from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from boostedchatScrapper.spiders.instagram_booksy import InstagramSpider
# Create your views here.

class InstagramScrapper(APIView):
    def post(self,request):
        accounts = request.data.get("accounts",[])
        followers = request.data.get("get_followers")
        inst = InstagramSpider()
        # inst.insert_data_with_enriched_outsourced_data(accounts,followers)
        inst.enrich_outsourced_data()
        # for account in accounts:
        #     print(account.lower())
        #     try:
        #         users = inst.get_ig_user_info(account.lower(),followers)
        #         try:
        #             inst.enrich_outsourced_data(tuple(users[0]),infinite= True)
        #         except Exception as error:
        #             print(error)
        #     except Exception as error:
        #         print(error)

        return Response({"success":True},status=status.HTTP_200_OK)