from airflow import DAG
from airflow.decorators import task
from datetime import datetime

with DAG("bojijo",start_date=datetime(2024,1,1),schedule_interval="@weekly",
        catchup=False) as dag:

        @task
        def extract(stock):
            return stock

        extract