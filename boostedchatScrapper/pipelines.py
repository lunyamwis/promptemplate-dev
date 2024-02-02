# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import json
from itemadapter import ItemAdapter
# from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


class BoostedchatscrapperPipeline:
    pass
    # def __init__(self) -> None:
        
    #     self.engine = create_engine(URL(
    #                         account = os.getenv('SF_ACCOUNT_IDENTIFIER'),
    #                         user = os.getenv('SF_USERNAME'),
    #                         password = os.getenv('SF_PASSWORD'),
    #                         database = os.getenv('SF_DATABASE'),
    #                         schema = os.getenv('SF_SCHEMA'),
    #                         warehouse = os.getenv('SF_WAREHOUSE'),
    #                         role=os.getenv('SF_ROLE'),
    #                 ))
    #     self.connection = self.engine.connect()
    #     print("=====================snowflaketester⭐⭐⭐=====================================")
    #     result = self.connection.execute("select * from INSTAGRAM_ACCOUNT;")
    #     for row in result:
    #         print(row)
    #     print("======================snowflaketester⭐⭐⭐⭐====================================")

    # def process_item(self, item, spider):
    #     result = self.connection.execute("select * from INSTAGRAM_ACCOUNT;")
    #     print("=====================snowflaketest⭐=====================================")
    #     print(result)
    #     print("======================snowflaketest⭐====================================")
    #     with Session(self.engine) as session:
    #         session.begin()  # <-- required, else InvalidRequestError raised on next call
    #         print("=====================snowflaketest⭐⭐⭐⭐⭐⭐⭐⭐=====================================")
    #         print(result)
    #         print("======================snowflaketest⭐⭐⭐⭐⭐⭐⭐⭐====================================")
    #         if "name" in item.keys():
    #             print("=====================snowflaketest⭐⭐⭐⭐⭐⭐⭐⭐=====================================")
    #             print(item)
    #             print("======================snowflaketest⭐⭐⭐⭐⭐⭐⭐⭐====================================")
    #             session.execute(f"""insert into INSTAGRAM_OUTSOURCEDINFO (SOURCE, RESULTS) values ('{item["name"]}','{str(json.dumps(item))}')""")
    #             session.commit()
                
    #         session.close()

    #     return item
    
    # def close_spider(self, spider):

    #     ## Close cursor & connection to database 
    #     self.connection.close()
    #     self.engine.dispose()
        