from celery import shared_task
from boostedchatScrapper.spiders.instagram_booksy import InstagramSpider


@shared_task()
def scrap_instagram(accounts,followers):
    inst = InstagramSpider()
    # inst.insert_data_with_enriched_outsourced_data(accounts,followers)
    for account in accounts:
        print(account.lower())
        try:
            users = inst.get_ig_user_info(account.lower(),followers)
            try:
                inst.enrich_outsourced_data(tuple(users[0]),infinite= True)
            except Exception as error:
                print(error)
        except Exception as error:
            print(error)
    inst.enrich_outsourced_data()