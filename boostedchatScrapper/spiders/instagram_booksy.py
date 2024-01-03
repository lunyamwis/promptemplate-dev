import time
import json
import uuid
import sys
import os
import re
import random
import pandas as pd
current_dir = os.getcwd()




# Add the current directory to sys.path
sys.path.append(current_dir)
import concurrent.futures
from .helpers.instagram_login_helper import login_user
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from kafka import KafkaProducer
from collections import ChainMap
from .constants import STYLISTS_WORDS
from sqlalchemy import create_engine, text
# from boostedchatScrapper.spiders.instagram import InstagramSpider
# insta_spider = InstagramSpider()
# insta_spider.get_followers('colorswithchemistry')

# producer = KafkaProducer(bootstrap_servers=['localhost:9092'], value_serializer=lambda v: json.dumps(v).encode('utf-8'))
def bytes_encoder(o):
    if isinstance(o, bytes):
        return o.decode('utf-8')  # Or encode to base64, etc.
    if isinstance(o, str):
        return str.replace("'","")
    raise TypeError



class InstagramSpider:
    name = 'instagram'
    db_url = "postgresql+psycopg2://postgres:boostedchatdb@localhost:5432/booksyus"
    engine = create_engine(db_url)
    connection = engine.connect()

    # def send_scrape_task(self, username):
    #     task = {'task_type': 'scrape_followers', 'username': username}
    #     producer.send('scrapingtasks', value=task)
    def get_usernames(self, path, column):
        df = pd.read_csv(path)
        pattern = r'https://(?:www\.)?instagram\.com/([^/]+)'
        df['username'] = df[column].str.extract(pattern, flags=re.IGNORECASE)
        df['username'].fillna(df[column], inplace=True)
        return list(df['username'])

    def get_users(self, query):
        client = login_user(username='matisti96', password='luther1996-')
        users = client.search_users(query)
        return users
    
    def get_hashtag_users(self, query):
        client = login_user(username='matisti96', password='luther1996-')
        hashtags = client.hashtag_medias_top_v1(query, amount=10)
        return [hashtag.user.username for hashtag in hashtags]


    def get_similar_accounts(self, username):
        client = login_user(username='matisti96', password='luther1996-')
        user_id = client.user_id_from_username(username=username)
        
        return client.fbsearch_suggested_profiles(user_id=user_id)
        
    

    def get_featured_accounts(self, username):
        client = login_user(username='matisti96', password='luther1996-')
        user_id = client.user_id_from_username(username=username)
        return client.featured_accounts_v1(target_user_id=user_id)

    def get_family_accounts(self, username):
        client = login_user(username='matisti96', password='luther1996-')
        user_id = client.user_id_from_username(username=username)
        return client.get_account_family_v1(target_user_id=user_id)
    
    def handle_outsourced(self,username):
        client = login_user(username='matisti96', password='luther1996-')
        instagram_accounts_ = self.connection.execute(text("SELECT id FROM instagram_account;"))
        instagram_names_ = self.connection.execute(text("SELECT igname FROM instagram_account;"))
        instagram_names = instagram_names_.fetchall()
        instagram_accounts = instagram_accounts_.fetchall()
        for i, instagram_account in enumerate(instagram_accounts_.fetchall()):
            print(f"{i}-> {instagram_account}")
            try:
                try:
                    user_info = client.user_info_by_username(instagram_names[i][0])
                except Exception as error:
                    user_info = {}
                    print(error)
                # import pdb;pdb.set_trace()
                json_string = json.dumps(user_info.dict(), default=bytes_encoder)
                self.connection.execute(text(f"""
                    INSERT INTO instagram_outsourced (deleted_at,id,created_at,updated_at, source,results,account_id)
                    VALUES (DEFAULT, '{str(uuid.uuid4())}','{datetime.now(timezone.utc)}','{datetime.now(timezone.utc)}',
                    'instagram','{json_string.replace("'", "")}','{instagram_account[0]}'
                    )

                """))
            except Exception as error:
                print(error)
   
    def get_ig_user_info(self, username):
        client = login_user(username='matisti96', password='luther1996-')
        user_info = client.user_info_by_username(username)
        user_id = user_info.pk

        batch_size = 100  # Adjust this based on your needs
        def process_similar_accounts(offset):
            # Loop to retrieve followers in batches
            # _, cursor = client.user_followers_v1_chunk(user_id, max_amount=batch_size)
            # followers, cursor = client.user_followers_v1_chunk(user_id, max_amount=batch_size, max_id=cursor)
            # followers = client.user_followers(user_id=user_id,amount=batch_size)
            inserted_ids = []
            followers = client.fbsearch_suggested_profiles(user_id=user_id)


            # # print(followers)
            # # TODO: save followers to database
            for i,follower in enumerate(followers):
                print(follower['username'])

                # Assuming 'igname' is the variable containing the Instagram name you want to insert
                igname = follower['username']

                # Check if igname already exists in the table
                name = 'on_hold'
                # get_on_hold_status = self.connection.execute(text(f"SELECT id FROM instagram_statuscheck WHERE name = %s", (name,)))
                # get_on_hold_status_id = get_on_hold_status.fetchone()
                try:
                    check_instagram_accounts = self.connection.execute(text(f"SELECT id FROM instagram_account WHERE igname = '{igname}'"))
                    # self.connection.commit()
                    # import pdb;pdb.set_trace()
                    
                    existing_id = check_instagram_accounts.fetchone()
                    inserted_id = None

                    if existing_id:
                        print(f"The igname '{igname}' already exists with ID {existing_id}. Skipping insertion.")
                    else:
                        # Perform the INSERT operation
                        try:
                            time.sleep(3)
                            insert_record_return_id = self.connection.execute(text(f"""
                                INSERT INTO instagram_account (
                                    deleted_at, id, created_at, updated_at, email, phone_number,
                                    profile_url, status_id, igname, full_name, assigned_to,
                                    dormant_profile_created, confirmed_problems, rejected_problems,qualified,index
                                )
                                VALUES (
                                    DEFAULT,'{str(uuid.uuid4())}', '{datetime.now(timezone.utc)}',
                                    '{datetime.now(timezone.utc)}', DEFAULT, DEFAULT, DEFAULT,
                                    DEFAULT, '{igname}', '{follower['full_name'].replace("'","")}', 'Robot',
                                    DEFAULT, DEFAULT, DEFAULT, '{False}',1
                                )
                                RETURNING id;
                                
                            """)) # implement algorithm for checking timecap
                            self.connection.commit()
                            print("--------------------INSERRTED----------------------")
                        except Exception as error:
                            print(error)

                        inserted_id = insert_record_return_id.fetchone()[0]
                        inserted_ids.append(inserted_id)

                    if inserted_id:
                        print(f"Inserted new record with ID {inserted_id}.")
                        try:
                            # insert_ = inserted_id.fetchone()[0]
                            get_igname = self.connection.execute(text(f"""
                                select igname from instagram_account where id='{inserted_id}';
                            """))
                            user_information = client.user_info_by_username(get_igname.fetchone()[0])
                            self.connection.execute(text(f"""
                                INSERT INTO instagram_outsourced (deleted_at,id,created_at,updated_at, source,results,account_id)
                                VALUES (DEFAULT, '{str(uuid.uuid4())}','{datetime.now(timezone.utc)}','{datetime.now(timezone.utc)}',
                                'instagram','{json.dumps(user_information.dict(), default=bytes_encoder)}','{inserted_id}'
                                )

                            """))
                            self.connection.commit()
                            print("--------------------INSERRTED OUTSOURCED----------------------")
                        except Exception as error:
                            print(error)
                except Exception as err:
                    print(f"Error during database operation: {err}")

                    # Rollback the transaction to keep the database in a consistent state
                    self.connection.rollback()
            return inserted_ids

        def process_followers(offset):
            # Loop to retrieve followers in batches
            # _, cursor = client.user_followers_v1_chunk(user_id, max_amount=batch_size)
            # followers, cursor = client.user_followers_v1_chunk(user_id, max_amount=batch_size, max_id=cursor)
            followers = client.user_followers(user_id=user_id,amount=batch_size)
            # followers = client.fbsearch_suggested_profiles(user_id=user_id)


            # # print(followers)
            # # TODO: save followers to database
            # # import pdb;pdb.set_trace()
            for follower in followers:
                print(followers[follower].username)

                # Assuming 'igname' is the variable containing the Instagram name you want to insert
                igname = followers[follower].username

                # Check if igname already exists in the table
                name = 'on_hold'
                get_on_hold_status = self.connection.execute(text("SELECT id FROM instagram_statuscheck WHERE name = %s", (name,)))
                get_on_hold_status_id = get_on_hold_status.fetchone()

                check_instagram_accounts = self.connection.execute(text("SELECT id FROM instagram_account WHERE igname = %s", (igname,)))
                existing_id = check_instagram_accounts.fetchone()
                inserted_id = None

                if existing_id:
                    print(f"The igname '{igname}' already exists with ID {existing_id[0]}. Skipping insertion.")
                else:
                    # Perform the INSERT operation
                    try:
                        insert_record_return_id = self.connection.execute(text(f"""
                            INSERT INTO instagram_account (
                                deleted_at, id, created_at, updated_at, email, phone_number,
                                profile_url, status_id, igname, full_name, assigned_to,
                                dormant_profile_created, confirmed_problems, rejected_problems
                            )
                            VALUES (
                                DEFAULT,'{str(uuid.uuid4())}', '{datetime.now(timezone.utc)}',
                                '{datetime.now(timezone.utc)}', DEFAULT, DEFAULT, DEFAULT,
                                '{get_on_hold_status_id[0]}', '{igname}', '{followers[follower].full_name}', 'Robot',
                                DEFAULT, DEFAULT, DEFAULT
                            )
                            RETURNING id;
                            
                        """))
                    except Exception as error:
                        print(error)

                    inserted_id = insert_record_return_id.fetchone()[0]
                    print(f"Inserted new record with ID {inserted_id}.")


                if inserted_id:
                    try:
                        self.connection.execute(text(f"""
                            INSERT INTO instagram_outsourced (deleted_at,id,created_at,updated_at, source,results,account_id)
                            VALUES (DEFAULT, '{str(uuid.uuid4())}','{datetime.now(timezone.utc)}','{datetime.now(timezone.utc)}',
                            'instagram','{json.dumps(user_info.dict(), default=bytes_encoder)}','{inserted_id}'
                            )

                        """))
                    except Exception as error:
                        print(error)

                    
                    
                
        # Use ThreadPoolExecutor for parallel processing
        offsets = range(0, 1, 1)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            
            # executor.map(process_followers,offsets)
            results = list(executor.map(process_similar_accounts,offsets))
            # Optional: Add a delay if needed to prevent hitting rate limits
            print(results)
            time.sleep(2)  # Add a delay of 2 seconds between batches

        return results
            

    def get_action_button_info(self, username):
        client = login_user(username='matisti96', password='luther1996-')
        url_info = client.user_info_by_username(username)

        return urlparse(url_info.external_url).netloc
    

    def find_largest_count(self, data, count_type='like'):
        """
        Find the largest like count or like count from the given dataset.

        Parameters:
        - data: List of dictionaries containing 'like_count' and 'like_count' keys.
        - count_type: Specify 'like' or 'like' to determine which count to find.

        Returns:
        - The largest count value.
        """
        if count_type not in ('comment', 'like'):
            raise ValueError("Invalid count_type. Use 'comment' or 'like'.")

        # Get the key based on count_type
        count_key = f"{count_type}_count"

        # Find the largest count using a lambda function
        entry_with_largest_count = max(data, key=lambda x: x[count_key])

        return entry_with_largest_count

    def get_dates_within_last_seven_days(self, date_list):
        today = datetime.now(timezone.utc)
        seven_days_ago = today - timedelta(days=7)
        
        dates_within_last_seven_days = []

        for date in date_list:
            if seven_days_ago <= date <= today:
                dates_within_last_seven_days.append(date)
        

        return len(dates_within_last_seven_days) > 0
    

    def get_popularity(self, outsourced_data):
        if outsourced_data['follower_count'] > 5000:
            return "PRO"
        elif outsourced_data['follower_count'] >= 500 and outsourced_data['follower_count'] <= 5000:
            return "ACTIVE"
        elif outsourced_data['follower_count'] <= 300:
            return "INACTIVE"
        
    def get_metrics_check(self, lst):
        return {
            "pro" : any(item > 50 for item in lst),
            "active" : any(item >= 20 and item <= 50 for item in lst) and not any(item >= 50 for item in lst),
            "inactive" : any(item <= 20 for item in lst)
        }
        

    def check_keywords(self,outsourced_data):
        keyword_count = []
        for i in STYLISTS_WORDS:
            if i in str(outsourced_data['full_name']).lower():
                keyword_count.append(True)
            
            
            if i in str(outsourced_data['category']).lower():
                keyword_count.append(True)
            
            if i in str(outsourced_data['biography']).lower():
                keyword_count.append(True)
        
        return len(keyword_count) > 0
        

    def enrich_outsourced_data(self, users=None, infinite=False, changing_index=None):
        client = login_user(username='matisti96', password='luther1996-')
        outsourced_data_ = None
        if infinite:
            # import pdb;pdb.set_trace()
            outsourced_data_ = self.connection.execute(text(f"SELECT id, results, account_id FROM instagram_outsourced where account_id in {tuple(users)};"))
        else:
            outsourced_data_ = self.connection.execute(text("""
                    SELECT id, results, account_id 
                    FROM instagram_outsourced 
                    where account_id in (select id from instagram_account where status_id is null);
            """)
            )
        # import pdb;pdb.set_trace()
        outsourced_dataset = True
        ig_data_ = self.connection.execute(text("SELECT id, igname FROM instagram_account;"))
        ig_dataset = ig_data_.fetchall()
        

        def insert_information(inserted_id,igname):

            try:
                user_info = client.user_info_by_username(igname)
                self.connection.execute(text(f"""
                    INSERT INTO instagram_outsourced (deleted_at,id,created_at,updated_at, source,results,account_id,hour_to_be_executed)
                    VALUES (DEFAULT, '{str(uuid.uuid4())}','{datetime.now(timezone.utc)}','{datetime.now(timezone.utc)}',
                    'instagram','{json.dumps(user_info.dict(), default=bytes_encoder)}','{inserted_id}','0'
                    )

                """))
                print(f"inserted outsourced record for -------------{inserted_id}")
            except Exception as error:
                print(error)

        
            

        def outsourcing_information(changing_indice=None, accounts=48):
            now = datetime.now(timezone.utc)
            hr = now.hour - 6
            # hr = now.hour
            hour_idx = 12/accounts
            changing_idx = changing_indice
            end_prev_day = 20 - hr if hr < 20 else 12
            day_idx = 1 if hr < 20 else 2
            salesreps = None
            try:
                salesreps = self.connection.execute(text(
                    """
                    SELECT id FROM sales_rep_salesrep;
                    """
                )).fetchall()
            except Exception as error:
                print(error)
            for i, outsourced_data in enumerate(outsourced_data_.fetchall()):
                print(f"{i}->{outsourced_data[1]['username']}")
                try:
                    user_medias = client.user_medias(user_id=outsourced_data[1]['pk'],amount=2)
                    days_check = self.get_dates_within_last_seven_days([media.taken_at for media in user_medias])
                    popularity_check = self.get_popularity(outsourced_data[1])
                    keywords_chck = self.check_keywords(outsourced_data[1])
                    try:
                        outsourced_data[1].pop("is_posting_actively")
                        outsourced_data[1].pop("is_popular")
                        outsourced_data[1].pop("is_stylist")
                    except Exception as error:
                        print(error)
                    
                    media_components = []
                    for media in user_medias:
                        media_component = {
                            "id" : media.id,
                            "pk" : media.pk,
                            "comment_count" : media.comment_count,
                            "like_count" : media.like_count
                        }
                        media_components.append(media_component)
                    
                    media_id = self.find_largest_count(media_components, 'like')['id']
                    ext_url = outsourced_data[1].get("external_url")
                    has_book_button = False
                    if ext_url:
                        service_providers = ["booksy", "styleseat", "squire", "thecut", "vagaro"]
                        has_book_button = any(provider.lower() in ext_url.lower() for provider in service_providers)
                    else:
                        has_book_button = False
                    checks =  {
                        "is_posting_actively": days_check,
                        "is_popular":popularity_check,
                        "is_stylist": keywords_chck,
                        "book_button": has_book_button,
                        "media_id": media_id
                    }
                    enriched_outsourced_data = {**checks, **outsourced_data[1]}
                    
                    try:
                        json_string = json.dumps(enriched_outsourced_data, default=bytes_encoder)
                        self.connection.execute(text(f"""
                            UPDATE  instagram_outsourced SET results='{json_string.replace("'", "")}'
                            WHERE instagram_outsourced.id='{outsourced_data[0]}';
                        """))
                        print(f"updated record-------------{outsourced_data[0]}")
                        self.connection.commit()
                    except Exception as error:
                        print(error)
                        self.connection.rollback()

                    try:
                        is_stylist = enriched_outsourced_data.get('is_stylist', False)
                        is_private = enriched_outsourced_data.get('is_private', False)
                        is_popular = enriched_outsourced_data.get('is_popular', '')
                        if is_stylist and not is_private and (is_popular == 'ACTIVE' or is_popular == 'PRO'):
                            
                            self.connection.execute(text(f"""
                                    UPDATE instagram_account SET qualified = TRUE WHERE id='{outsourced_data[2]}';             
                                    """))
                            # perform round robin task here below
                            salesrep = salesreps[i % len(salesreps)]
                            salesrep_id = salesrep[0]

                            
                            self.connection.execute(text(
                                f"""
                                INSERT INTO sales_rep_salesrep_instagram (salesrep_id, account_id) 
                                VALUES ('{salesrep_id}', '{outsourced_data[2]}')
                                """
                            ))
                            self.connection.commit()
                            empty_dict= {}
                            print(f"hour_indice==============>{hour_idx}")
                            print(f"changing_indice===============>{changing_idx}")
                            crontab_id = None
                            if hour_idx > end_prev_day:
                                hour_idx += 11
                                end_prev_day += 24
                                day_idx += 1

                            time_to_be_executed = None
                            if changing_idx:
                                print(f"changing_indice_has_changed_to=================>{changing_idx + hour_idx}")
                                time_to_be_executed = now + timedelta(hours=changing_idx + hour_idx)
                            else:
                                time_to_be_executed = now + timedelta(hours=hour_idx)

                            hour_to_be_executed = time_to_be_executed.hour
                            day_to_be_executed = time_to_be_executed.day
                            month_to_be_executed = time_to_be_executed.month
                            random_minute = random.randint(1,60)

                            crontab_id = self.connection.execute(text(f"""
                                INSERT INTO django_celery_beat_crontabschedule (minute, hour, day_of_week , day_of_month, month_of_year, timezone ) 
                                VALUES ({random_minute},{hour_to_be_executed},'*',{day_to_be_executed},'{month_to_be_executed}', 'UTC') RETURNING id;
                            """))
                            hour_idx += 12/accounts

                            self.connection.execute(text(f"""
                                INSERT INTO django_celery_beat_periodictask (
                                    name, task, interval_id, crontab_id, args, kwargs, queue, enabled, last_run_at, total_run_count,
                                    date_changed, description, one_off, headers
                                )
                                VALUES (
                                    'SendFirstCompliment-{outsourced_data[1]['username']}',
                                    'instagram.tasks.send_first_compliment',NULL,'{crontab_id.fetchone()[0]}',
                                    '{json.dumps([[outsourced_data[1]['username']]])}', '{empty_dict}', NULL,
                                    TRUE, NULL, 0, NOW(), 'Your task description', TRUE, '{empty_dict}'
                                );
                            """))
                            self.connection.commit()
                            print("=================Inserted cronjob===================")
                    except Exception as error:
                        print(error)
                        self.connection.rollback()

                except Exception as error:
                    print(error)
                    # Rollback the transaction to keep the database in a consistent state
                    self.connection.rollback()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # import pdb;pdb.set_trace()
            if outsourced_dataset:
                executor.submit(outsourcing_information, changing_index)
            else:
                if not infinite:
                    for ig in ig_dataset:
                        executor.submit(insert_information,ig['id'],ig['igname'])
        

    def insert_data_with_enriched_outsourced_data(self):
        get_earliest_date = self.connection.execute(text("SELECT minute, hour, day_of_month, month_of_year FROM django_celery_beat_crontabschedule ORDER BY id ASC LIMIT 1;")).fetchone()
        get_latest_date = self.connection.execute(text("SELECT minute, hour, day_of_month, month_of_year FROM django_celery_beat_crontabschedule ORDER BY id DESC LIMIT 1;")).fetchone()
        now = datetime.now(timezone.utc)
        latest_date = datetime(
                            now.year, 
                            int(get_latest_date[3]),  #month
                            int(get_latest_date[2]), #day
                            int(get_latest_date[1]), #hour
                            int(get_latest_date[0]) #minute
                        )
        earliest_date = datetime(
                            now.year, 
                            int(get_earliest_date[3]),  #month
                            int(get_earliest_date[2]), #day
                            int(get_earliest_date[1]), #hour
                            int(get_earliest_date[0]) #minute
                        )
        difference = latest_date - earliest_date
        changing_idx = int((difference.total_seconds() / 60) / 60)
        print(f"changing_indice===============>{changing_idx}")
        i = 0
        while True:

            ig_data = self.connection.execute(text("SELECT id, igname FROM instagram_account WHERE qualified=TRUE ORDER BY RANDOM();"))
            ig_dataset = ig_data.fetchall()
            print(f"Number_of_qualified_accounts-----------{len(ig_dataset)}")
            # import pdb;pdb.set_trace()
            for j, user in enumerate(ig_dataset):
                print(f"User-----{user[1]}")
                try:
                    new_users = self.get_ig_user_info(user[1])
                    users = []
                    if new_users:
                        for _ in new_users:
                            for x, new_user in enumerate(_):
                                users.append(new_user)

                    if j == 0:
                        self.enrich_outsourced_data(users, infinite=True, changing_index=changing_idx)

                    if j > 1:
                        self.enrich_outsourced_data(users, infinite=True, changing_index=changing_idx + len(users))
                        print(f"changing_index_in_infinite_loop=================>{changing_idx + len(users)}")
                    
                except Exception as error:
                    print(error)
                
                
            
            print(f"Iteration---------{i}")
            
            i += 1



    

