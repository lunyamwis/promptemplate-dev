from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from boostedchatScrapper.spiders.instagram_booksy import InstagramSpider
# Create your views here.

class InstagramScrapper(APIView):
    def post(self,request):
        accounts = request.data.get("accounts",[])
        inst = InstagramSpider()
        for account in accounts:
            try:
                users = inst.get_ig_user_info(account)
                try:
                    inst.enrich_outsourced_data(users,infinite= True)
                except Exception as error:
                    print(error)
            except Exception as error:
                print(error)

        return Response({"success":True},status=status.HTTP_200_OK)