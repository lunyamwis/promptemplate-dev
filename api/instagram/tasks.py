from celery import shared_task
import pandas as pd
import os
from boostedchatScrapper.spiders.instagram import InstagramSpider
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user


db_url = f"postgresql://{os.getenv('POSTGRES_USERNAME')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNAME')}"
load_tables = True

@shared_task()
def scrap_followers(username,delay):
    inst = InstagramSpider(load_tables=load_tables,db_url=db_url)
    inst.scrap_followers(username,delay)

@shared_task()
def scrap_users(query):
    inst = InstagramSpider(load_tables=load_tables,db_url=db_url)
    inst.scrap_users(query)
    
@shared_task()
def scrap_info(delay_before_requests,delay_after_requests,step,accounts,round):
    inst = InstagramSpider(load_tables=load_tables,db_url=db_url)
    inst.scrap_info(delay_before_requests,delay_after_requests,step,accounts,round)
    
@shared_task()
def insert_and_enrich(account_data,outsourced_data,keywords_to_check):
    inst = InstagramSpider(load_tables=load_tables,db_url=db_url)
    inst.insert_and_enrich(account_data,outsourced_data,keywords_to_check)
    
