"""
Складываем курс валют в GreenPlum
"""

from airflow import DAG
from airflow.utils.dates import days_ago
import logging
import csv
import xml.etree.ElementTree as ET

from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators.bash import BashOperator
from airflow.operators.python_operator import PythonOperator

DEFAULT_ARGS = {
    'start_date': days_ago(2),
    'owner': 'a-morshinin',
    'poke_interval': 600
}

# TODO: вынести url, файлы с xml и csv в константу


dag = DAG("a_morshinin_load_cbr",
          schedule_interval='@daily',
          default_args=DEFAULT_ARGS,
          max_active_runs=1,
          tags=['a-morshinin']
          )

# TODO: Не константа, а {{ format_ds... }}
# TODO: удалять файл a_morshinin_cbr.xml, если он уже есть
load_cbr_xml_script = '''
curl https://www.cbr.ru/scripts/XML_daily.asp?date_req=01/11/2021 | iconv -f Windows-1251 -t UTF-8 > /tmp/a_morshinin_cbr.xml
'''

load_cbr_xml = BashOperator(
    task_id='load_cbr_xml',
    bash_command=load_cbr_xml_script,
    dag=dag
)


def export_xml_to_csv_func():
    parser = ET.XMLParser(encoding="UTF-8")
    tree = ET.parse('/tmp/a_morshinin_cbr.xml', parser=parser)
    root = tree.getroot()

    with open('/tmp/a_morshinin_cbr.csv', 'w') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for Valute in root.findall('Valute'):
            NumCode = Valute.find('NumCode').text
            CharCode = Valute.find('CharCode').text
            Nominal = Valute.find('Nominal').text
            Name = Valute.find('Name').text
            Value = Valute.find('Value').text
            writer.writerow([root.attrib['Date']] + [Valute.attrib['ID']] + [NumCode] + [CharCode] + [Nominal] +
                            [Name] + [Value.replace(',', '.')])
            logging.info([root.attrib['Date']] + [Valute.attrib['ID']] + [NumCode] + [CharCode] + [Nominal] +
                         [Name] + [Value.replace(',', '.')])


export_xml_to_csv = PythonOperator(
    task_id='export_xml_to_csv',
    python_callable=export_xml_to_csv_func,
    dag=dag
)


def load_csv_to_gp_func():
    pg_hook = PostgresHook('conn_greenplum_write')
    # TODO: Мёрдж или очищение предыдущего батча
    pg_hook.copy_expert("COPY a_morshinin_cbr FROM STDIN DELIMITER ','", '/tmp/a_morshinin_cbr.csv')


load_csv_to_gp = PythonOperator(
    task_id='load_csv_to_gp',
    python_callable=load_csv_to_gp_func,
    dag=dag
)

load_cbr_xml >> export_xml_to_csv >> load_csv_to_gp
