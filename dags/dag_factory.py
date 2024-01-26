from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'dag_generator_dag',
    default_args=default_args,
    description='DAG to run dag_generator',
    schedule_interval=None,  # Set the schedule_interval according to your needs
)

dag_generator_task = BashOperator(
    task_id='run_dag_generator',
    bash_command='python manage.py dag_generator',
    dag=dag,
)

dag_generator_task