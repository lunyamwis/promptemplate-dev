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

from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Dictionary(Base):
    __tablename__ = 'dictionary'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    response = Column(JSON)

class BoostedchatscrapperPipeline:
    def __init__(self):
        # Connection Details
        db_url = f"postgresql://{os.getenv('POSTGRES_USERNAME_ETL')}:{os.getenv('POSTGRES_PASSWORD_ETL')}@{os.getenv('POSTGRES_HOST_ETL')}:{os.getenv('POSTGRES_PORT_ETL')}/{os.getenv('POSTGRES_DBNAME_ETL')}"

        # Create engine
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)

        # Create session
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def process_item(self, item, spider):
        # Create new dictionary object
        dictionary_entry = Dictionary(name=item['name'], response=item['resp_meta'])

        # Add dictionary object to session
        self.session.add(dictionary_entry)
        
        # Commit changes to the database
        self.session.commit()

        return item

    def close_spider(self, spider):
        # Close the session
        self.session.close()
