from airflow import DAG
from airflow.decorators import task
from datetime import datetime

with DAG("ontwekas",start_date=datetime(2024,1,1),schedule_interval="@daily",
        catchup=False) as dag:

        @task
        def extract(stock):
            return stock

        extract