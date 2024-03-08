from celery import shared_task
import pandas as pd
from boostedchatScrapper.spiders.instagram import InstagramSpider
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user




@shared_task()
def scrap_followers(username,delay):
    inst = InstagramSpider()
    inst.scrap_followers(username,delay)

@shared_task()
def scrap_users(query):
    inst = InstagramSpider()
    inst.scrap_users(query)
    
@shared_task()
def scrap_info(delay_before_requests,delay_after_requests,step,accounts,round):
    inst = InstagramSpider()
    inst.scrap_info(delay_before_requests,delay_after_requests,step,accounts,round)
    
@shared_task()
def insert_and_enrich(account_data,outsourced_data,keywords_to_check):
    inst = InstagramSpider()
    inst.insert_and_enrich(account_data,outsourced_data,keywords_to_check)
    
