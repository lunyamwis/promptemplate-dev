from celery import shared_task
import pandas as pd
from boostedchatScrapper.spiders.instagram_booksy import InstagramSpider
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user

@shared_task()
def scrap_instagram(accounts,followers):
    inst = InstagramSpider()
    # inst.insert_data_with_enriched_outsourced_data(accounts,followers)
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
    inst.enrich_outsourced_data()


@shared_task()
def process_followers_dry(client, cursor, username):
    rounds = 0
    while True:
        followers, cursor = client.user_followers_gql_chunk(client.user_id_from_username(username), max_amount=100,end_cursor=cursor)
        print(len(followers))
        data = []
        count = 0
        for follower in followers:
            data.append(client.user_info_by_username(follower.username).dict())
            print(f"{count+1}==================>{follower.username}")
        df = pd.DataFrame(data)
        df.to_csv('full_output.csv', mode='a', header=None, index=False)
        print(f"{rounds+1}==================>{len(data)}")
