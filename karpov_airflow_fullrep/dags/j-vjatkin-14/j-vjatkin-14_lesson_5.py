"""
Am Operator and DAG for fetching data from RaM API
by Yuri Vyatkin, 2022
"""

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from j_vjatkin_14_plugins.j_vjatkin_14_ram import VjatkinRamLocationOperator
from airflow.hooks.postgres_hook import PostgresHook
from airflow.utils.dates import days_ago

DEFAULT_ARGS = {
    'start_date': days_ago(10),
    'owner': 'j-vjatkin',
    'poke_interval': 600
    }

with DAG('j-vjatkin_lesson_5',
     schedule_interval=None,
     default_args=DEFAULT_ARGS,
     max_active_runs=1,
     tags=['j-vjatkin']) as dag:

    def write_data_to_db(ti):
        data = ti.xcom_pull(key='return_value', task_ids='get_top_3_locations')

        pg_hook = PostgresHook(postgres_conn_id='conn_greenplum_write')
        preprocessed_values = [f"({x['id']}, '{x['name']}', '{x['type']}', '{x['dimension']}', {x['residents']})" for x in data]

        create_table_command = f"""
                CREATE TABLE IF NOT EXISTS j_vjatkin_ram_location (
                    id SERIAL4 PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    type VARCHAR NOT NULL,
                    dimension VARCHAR NOT NULL,
                    resident_cnt INT4 NOT NULL);
            """,
        truncate_command = "TRUNCATE TABLE j_vjatkin_ram_location"
        insert_command = f"INSERT INTO j_vjatkin_ram_location VALUES {','.join(preprocessed_values)}"
        pg_hook.run(create_table_command, False)
        pg_hook.run(truncate_command, False)
        pg_hook.run(insert_command, False)

    get_top_3_locations = VjatkinRamLocationOperator(
        task_id='get_top_3_locations',
        locations_number=3
    )

    write_locations_to_db = PythonOperator(
        task_id='write_locations_to_db',
        python_callable=write_data_to_db
    )

    get_top_3_locations >> write_locations_to_db
