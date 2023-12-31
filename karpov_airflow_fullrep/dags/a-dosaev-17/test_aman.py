"""
Тестовый даг
"""
import logging

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago

DEFAULT_ARGS = {
    'start_date': days_ago(2),
    'owner': 'a-dosaev-17',
    'poke_interval': 600
}

with DAG("aman_test",
    schedule_interval='@daily',
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    tags=['a-dosaev-17']
) as dag:

    dummy = DummyOperator(task_id="dummy")

    echo_ds = BashOperator(
        task_id='echo_ds',
        bash_command='echo {{ a-dosaev-17 }}',
        dag=dag
    )

    def hello_world_func():
        logging.info("Hello World!")

    hello_world = PythonOperator(
        task_id='hello_world',
        python_callable=hello_world_func,
        dag=dag
    )

    dummy >> [echo_ds, hello_world]