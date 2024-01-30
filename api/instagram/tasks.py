from celery import shared_task
import pandas as pd
from boostedchatScrapper.spiders.instagram_booksy import InstagramSpider
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user

@shared_task()
def scrap_followers_or_similar_accounts(accounts,followers,positive_keywords,negative_keywords):
    print(accounts)
    inst = InstagramSpider()
    for account in accounts:
        print(account.lower())
        try:
            users = inst.get_ig_user_info(account.lower(),followers)
            try:
                inst.enrich_outsourced_data(tuple(users[0]),infinite= True,positive_keywords=positive_keywords,
                                            negative_keywords=negative_keywords)
            except Exception as error:
                print(error)
        except Exception as error:
            print(error)
    

@shared_task()
def scrap_followers_into_csv(cursor, user_id):
    client = login_user(username='matisti96', password='luther1996-')
    rounds = 0
    while True:
        followers, cursor = client.user_followers_gql_chunk(client.user_id_from_username(user_id), max_amount=5,end_cursor=cursor)
        print(len(followers))
        data = []
        count = 0
        for follower in followers:
            data.append(client.user_info_by_username(follower.username).dict())
            count += 1
            print(f"User: {count}==================>{follower.username}")
            df = pd.DataFrame(data)
            df.to_csv('full_output.csv', mode='a', header=None, index=False)
        
        print(f"Round: {rounds}==================>{len(data)}")
        rounds += 1