from airflow import DAG
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.sensors.http_sensor import HttpSensor
from airflow.utils.dates import days_ago
from datetime import timedelta
import json

dag = DAG(
    "get_followers",
    schedule_interval="10 10 29 1 *",
    start_date=days_ago(1),
    catchup=False,
)

# Define the HTTP operator
http_task = SimpleHttpOperator(
    task_id='http_task',
    http_conn_id='your_http_connection',  # Specify the HTTP connection ID
    endpoint='instagram/scrapFollowersOrSimilarAccounts/',  # Specify the endpoint to hit
    method='POST',  # Specify the HTTP method
    headers={'Content-Type': 'application/json'}, # Add any headers if needed
    data=json.dumps({'accounts': ['Booksybiz', 'Wahlpro', 'Titanbarber', 'Official cuts', 'Unitedbyshorthair', 'Behindthechair', 'Ruelrockstar', 'Underratedbarbers', 'Humblythegreatest', 'Arodpr23', 'Phillipwolf'], 'get_followers': 1}),  # Add any data if needed
    log_response=True,  # Log the response in the Airflow UI
    dag=dag,
)

# Set up task dependencies
http_task