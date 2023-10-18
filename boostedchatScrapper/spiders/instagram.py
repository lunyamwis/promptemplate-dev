import time
from .helpers.instagram_login_helper import login_user
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

class InstagramSpider:
    name = 'instagram'



    def get_users(self, query):
        client = login_user(username='nyambanemartin', password='nyambane1996-')
        users = client.search_users(query)
        return users
    
    def get_hashtag_users(self, query):
        client = login_user(username='nyambanemartin', password='nyambane1996-')
        hashtags = client.hashtag_medias_top_v1(query, amount=10)
        return [hashtag.user.username for hashtag in hashtags]


    def get_similar_accounts(self, username):
        client = login_user(username='nyambanemartin', password='nyambane1996-')
        user_id = client.user_id_from_username(username=username)
        
        return client.fbsearch_suggested_profiles(user_id=user_id)
        
    

    def get_featured_accounts(self, username):
        client = login_user(username='nyambanemartin', password='nyambane1996-')
        user_id = client.user_id_from_username(username=username)
        return client.featured_accounts_v1(target_user_id=user_id)

    def get_family_accounts(self, username):
        client = login_user(username='nyambanemartin', password='nyambane1996-')
        user_id = client.user_id_from_username(username=username)
        return client.get_account_family_v1(target_user_id=user_id)
        
    def get_followers(self,username):

        # Log in to your Instagram account
        client = login_user(username='nyambanemartin', password='nyambane1996-')

        # Get the followers of a specific user
        user_info = client.user_info_by_username(username)
        user_id = user_info.pk

        # Define batch size
        batch_size = 5  # You can adjust this based on your needs

        followers = None

        # Loop to retrieve followers in batches
        for offset in range(0, int(user_info.follower_count), batch_size):
            end_offset = min(offset + batch_size, int(user_info.follower_count))
            print(f'Retrieving followers {offset+1} to {end_offset}...')

            # Retrieve followers for the current batch
            followers = client.user_followers(user_info.pk, amount=batch_size)

            # Process the followers in this batch
            for follower in followers:
                # import pdb;pdb.set_trace()
                print(f'Username: {followers[follower].username}, Full Name: {followers[follower].full_name}, ID: {followers[follower].pk}')
            
            if offset == batch_size:
                batch_size*=2

            # Optional: Add a delay if needed to prevent hitting rate limits
            time.sleep(5)  # Add a delay of 2 seconds between batches

        return followers

    def get_action_button_info(self, username):
        client = login_user(username='nyambanemartin', password='nyambane1996-')
        url_info = client.user_info_by_username(username)

        return urlparse(url_info.external_url).netloc
    

    def get_dates_within_last_seven_days(self, date_list):
        today = datetime.now(timezone.utc)
        seven_days_ago = today - timedelta(days=7)
        
        dates_within_last_seven_days = []

        for date in date_list:
            if seven_days_ago <= date <= today:
                dates_within_last_seven_days.append(date)
        

        return len(dates_within_last_seven_days) > 0
    

    def get_popularity(self, username):
        # Log in to your Instagram account
        client = login_user(username='nyambanemartin', password='nyambane1996-')

        # Get the followers of a specific user
        user_info = client.user_info_by_username(username)
        return  {
            "pro": user_info.follower_count > 5000,
            "active": user_info.follower_count >= 500 and user_info.follower_count <= 5000,
            "inactive": user_info.follower_count <= 500
        }

    def get_metrics_check(self, lst):
        return {
            "pro" : any(item > 50 for item in lst),
            "active" : any(item >= 20 and item <= 50 for item in lst) and not any(item >= 50 for item in lst),
            "inactive" : any(item <= 20 for item in lst)
        }
        


    def get_is_social_media_active(self, username):
        client = login_user(username='nyambanemartin', password='nyambane1996-')
        user_id = client.user_id_from_username(username=username)
        user_medias = client.user_medias(user_id=user_id,amount=5)
        days_check = self.get_dates_within_last_seven_days([media.taken_at for media in user_medias])
        comments_check = self.get_metrics_check([media.comment_count for media in user_medias])
        # likes_check = self.get_metrics_check([media.like_count for media in user_medias])
        popularity_check = self.get_popularity(username=username)
        return {
            "pro": days_check  and popularity_check['pro'] or comments_check['pro'],
            "active": days_check and popularity_check['active'] and  comments_check['active'],
            "inactive": days_check and popularity_check['inactive'] and comments_check['inactive']
        }
    



    

