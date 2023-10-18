import time
from .helpers.instagram_login_helper import login_user
from urllib.parse import urlparse

class InstagramSpider:
    name = 'instagram'




    def get_followers(self,username):

        # Log in to your Instagram account
        client = login_user(username='nyambanemartin', password='nyambane1996-')

        # Get the followers of a specific user
        user_info = client.user_info_by_username(username)
        user_id = user_info.pk

        # Define batch size
        batch_size = 5  # You can adjust this based on your needs

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



    def get_action_button_info(self, username):
        client = login_user(username='nyambanemartin', password='nyambane1996-')
        url_info = client.user_info_by_username(username)

        return urlparse(url_info.external_url).netloc
    

    def get_social_media_active_nature(self, username):
        client = login_user(username='nyambanemartin', password='nyambane1996-')
        user_id = client.user_id_from_username(username=username)
        user_medias = client.user_medias(user_id=user_id,amount=5)
        return user_medias