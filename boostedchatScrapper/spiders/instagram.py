import time
import json
import uuid
import sys
import os
import re
import random
import logging
import pandas as pd
current_dir = os.getcwd()




# Add the current directory to sys.path
sys.path.append(current_dir)
import concurrent.futures
from .helpers.instagram_login_helper import login_user
from datetime import datetime, timedelta
from django.utils import timezone
from urllib.parse import urlparse
from kafka import KafkaProducer
from collections import ChainMap
from .constants import STYLISTS_WORDS,STYLISTS_NEGATIVE_WORDS
from sqlalchemy import create_engine, text,Table,MetaData,select,update
from api.instagram.models import InstagramUser
from api.scout.models import Scout,Device
from django.db.models import Q

class InstagramSpider:
    name = 'instagram'
    db_url = f"postgresql://{os.getenv('POSTGRES_USERNAME')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNAME')}"
    engine = create_engine(db_url)
    connection = engine.connect()
    transaction = connection.begin()
    metadata = MetaData()
    instagram_account_table = Table('instagram_account', metadata, autoload_with=engine)
    instagram_outsourced_table = Table('instagram_outsourced',metadata, autoload_with=engine)
    django_celery_beat_crontabschedule_table = Table('django_celery_beat_crontabschedule', metadata, autoload_with=engine)
    django_celery_beat_periodictask_table = Table('django_celery_beat_periodictask', metadata, autoload_with=engine)
    salesrep_table = Table('sales_rep_salesrep',metadata,autoload_with=engine)
    salesrep_instagram_table = Table('sales_rep_salesrep_instagram',metadata,autoload_with=engine)

    
    def store(self,users,source=1,linked_to='no_one',round=0):
        for user in users:
            InstagramUser.objects.create(username = user.username,info = user.dict(),source=source,linked_to=linked_to,round=round)

    def is_cursor_available(self):
        is_cursor_available = InstagramUser.objects.filter(Q(username__isnull=True) & Q(cursor__isnull=False))
        if is_cursor_available.exists():
            cursor = is_cursor_available.latest('created_at')
        return cursor

    def scrap_followers(self,username,delay):
        scouts = Scout.objects.filter(available=True)
        scout_index = 0
        initial_scout = scouts[scout_index]
        try:
            client = login_user(initial_scout)
        except Exception as error:
            print("There was an error logging in")
        
        user_info = client.user_info_by_username(''.join(username))
        time.sleep(delay)
        steps = user_info.follower_count/12
        
        try:
            followers,cursor = client.user_followers_gql_chunk(user_info.pk, max_amount=3)
        except Exception as error:
            InstagramUser.objects.create(cursor=cursor)
            print(error)

        self.store(followers)
        time.sleep(delay)
        if self.is_cursor_available:
            cursor = cursor
        for i in range(int(steps)-1):
            time.sleep(random.randint(delay,delay*2))
            try:
                followers, cursor = client.user_followers_gql_chunk(user_info.pk, max_amount=5,end_cursor=cursor)
            except Exception as error:
                InstagramUser.objects.create(cursor=cursor)
            self.store(followers)

    def scrap_users(self,query):
        scouts = Scout.objects.filter(available=True)
        scout_index = 0
        initial_scout = scouts[scout_index]
        client = login_user(scout=initial_scout)
        time.sleep(random.randint(4,10))
        users = client.search_users_v1(query,count=3)
        self.store(users)
       
    def scrap_extra(self, url, params, return_val):
        scouts = Scout.objects.filter(available=True)
        scout_index = 0
        initial_scout = scouts[scout_index]
        client = login_user(scout=initial_scout)
        result = client.private_request(url, params=params)
        self.store(result[return_val])    
        return result[return_val]
   
    def scrap_info(self,delay_before_requests,delay_after_requests,step,accounts,round):
        scouts = Scout.objects.filter(available=True)
        scout_index = 0
        initial_scout = scouts[scout_index]
        try:
            client = login_user(initial_scout)
        except Exception as error:
            print("There was an error logging in")
        
        instagram_users = InstagramUser.objects.filter(round=round)
        print(len(instagram_users))
        # val = 10 + 31 + 45 + 3 + 35 + 6
        for i, user in enumerate(instagram_users, start=1):
            print(i)
            if user.username:
                time.sleep(random.randint(delay_before_requests,delay_before_requests+step))
                try:
                    user.info = client.user_info_by_username(user.username).dict()
                    user.save()
                except Exception as error:
                    user.outsourced_id_pointer=True
                    user.save()
                    print(error)
                
                if i % step == 0:
                    scout_index = (scout_index + 1) % len(scouts)
                    client = login_user(scouts[scout_index])
                if i % accounts == 0:
                    time.sleep(random.randint(delay_after_requests,delay_after_requests+step))

    
    @classmethod
    def custom_insert(self,instagram_user):
        record = None
        
        with self.engine.connect() as connection:
            existing_username_query = select([self.instagram_account_table]).where(
                self.instagram_account_table.c.igname == instagram_user.username
            )
            existing_username = self.engine.execute(existing_username_query).fetchone()
            # if not existing_username:
            try:
                insert_statement = self.instagram_account_table.insert().values({
                        'id': str(uuid.uuid4()),
                        'created_at':timezone.now(),
                        'updated_at':timezone.now(),
                        'igname':instagram_user.username,
                        'full_name': instagram_user.info['full_name'],
                        "email":"",
                        "phone_number":"",
                        "profile_url":"",
                        "igname":"",
                        "full_name":"",
                        "assigned_to":"Robot",
                        "dormant_profile_created":True,
                        "confirmed_problems":"",
                        "rejected_problems":"",
                        "qualified":False,
                        "index":1,
                        "linked_to":"not"
                }).returning(self.instagram_account_table.c.id)

                result = connection.execute(insert_statement)
                account = result.fetchone()
                insert_statement = self.instagram_outsourced_table.insert().values({
                        'id': str(uuid.uuid4()),
                        'created_at':timezone.now(),
                        'updated_at':timezone.now(),
                        "source":"ig",
                        'results':instagram_user.info,
                        'account_id':account['id'] 
                }).returning(self.instagram_outsourced_table.c.results)
                result = connection.execute(insert_statement)
                record = result.fetchone()
            except Exception as error:
                print(error)
        return record['results'] if record else None

    
    def assign_salesreps(self,username,index):
        
        with self.engine.connect() as connection:
            salesreps = None

            try:
                get_salesreps = select([self.salesrep_table]).where(
                    self.salesrep_table.c.available == True
                )

                results = connection.execute(get_salesreps)
                salesreps = results.fetchall()
                
                print(f"no_salesreps=================={len(salesreps)}")
            except Exception as error:
                print(error)
            
            salesrep_id = salesreps[index % len(salesreps)]['id']
            get_account = select([self.instagram_account_table]).where(
                self.instagram_account_table.c.igname == username
            )
            try:
                results = connection.execute(get_account)
                account = results.fetchone()
            except Exception as error:
                print(error)

            if account:
                insert_statement = self.salesrep_instagram_table.insert().values({
                    'salesrep_id': salesrep_id,
                    'account_id': account['id']
                })
                try:
                    connection.execute(insert_statement)
                except Exception as error:
                    print(error)
            else:
                print(f"Account {username} does not exist")
            
    def qualify(self, client_info, keywords_to_check,time_to_begin_outreach):
        qualified = False
        if client_info:
            keyword_found = any(
                len(str(value)) > 1 and keyword.lower() in str(value).lower()
                for value in client_info.values()
                for keyword in keywords_to_check
            )
            if keyword_found:
                with self.engine.connect() as connection:
                    crontab_data = {'minute':time_to_begin_outreach.minute,'hour':time_to_begin_outreach.hour,
                                    'day_of_week':'*','day_of_month':time_to_begin_outreach.day,
                                    'month_of_year':time_to_begin_outreach.month,'timezone':'UTC'}
                    crontab_statement = self.django_celery_beat_crontabschedule_table.insert().values(crontab_data).returning(self.django_celery_beat_crontabschedule_table.c.id)
                    result = connection.execute(crontab_statement)
                    crontab_id = result.fetchone()
                    if crontab_id:
                        periodic_data = {'name':f"SendFirstCompliment-{client_info['username']}",'task':'instagram.tasks.send_first_compliment','crontab_id':crontab_id['id'],
                                        'args':json.dumps([client_info['username']]),'kwargs':json.dumps({}),'enabled':True,'one_off':True,'total_run_count':0,'date_changed':datetime.now(),
                                        'description':'test','headers':json.dumps({})}
                        periodic_task_statement = self.django_celery_beat_periodictask_table.insert().values(periodic_data)
                        connection.execute(periodic_task_statement)
                        print(f"successfullyninsertedperiodictaskfor->{client_info['username']}")
                        qualified = True
        return qualified


    def insert_and_enrich(self,keywords_to_check,round):
        instagram_users = InstagramUser.objects.filter(round=round)
        hour = 0
        for i,instagram_user in enumerate(instagram_users):
            print(i)
            outsourced = self.custom_insert(instagram_user)
            hour += 0.5
            qualified = self.qualify(outsourced,keywords_to_check, datetime.now()+timedelta(hours=hour))
            if qualified:
                self.assign_salesreps(instagram_user.username,i)
