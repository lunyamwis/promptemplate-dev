from kafka import KafkaConsumer
from .instagram import InstagramSpider
import json



consumer = KafkaConsumer('scrapingtasks', bootstrap_servers=['localhost:9092'], value_deserializer=lambda m: json.loads(m.decode('utf-8')))
instagram_spider = InstagramSpider()
import pdb;pdb.set_trace()
print(consumer)

for message in consumer:
    print(message)
    task = message.value
    if task['task_type'] == 'scrape_followers':
        username = task['username']
        # Call your function to scrape followers here
        instagram_spider.get_followers(username)
