from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'thao_nguyen',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='supermarket_etl_pipeline',
    schedule='@daily', # <- Đổi thành schedule
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['de_final_project', 'supermarket'],
) as dag:

    start_task = EmptyOperator(task_id='start_pipeline')

    run_etl_task = BashOperator(
        task_id='run_etl_script',
        bash_command='pip install openpyxl && python /opt/airflow/dags/scripts/etl_pipeline.py',
    )

    end_task = EmptyOperator(task_id='end_pipeline')

    start_task >> run_etl_task >> end_task