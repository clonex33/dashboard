from datetime import datetime, timedelta
import os
import pandas as pd
from sqlalchemy import create_engine
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.exceptions import AirflowException
from airflow.configuration import conf

# Define the DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 5, 27),
    'retries': 0,
    'execution_timeout': timedelta(minutes=1),  # Fail if the task runs longer than 1 minute
}

dag = DAG(
    'data_processing_dag',
    default_args=default_args,
    description='A DAG to process website traffic data from a CSV file',
    schedule_interval=None,
    tags=['data-processing'],
)

# Function to read, clean, and process the CSV file, then save to the database
def process_csv_file(dag_id):
    input_filepath = 'data_set/Website_Logs.csv'

    if not os.path.exists(input_filepath):
        raise AirflowException(f"Input file does not exist: {input_filepath}")

    # Read the CSV file
    listings = pd.read_csv(input_filepath)

    # Add a new column for the DAG ID
    listings['dag_id'] = dag_id

        # Convert 'accessed_date' column to datetime
    listings['accessed_date'] = pd.to_datetime(listings['accessed_date'], errors='coerce')

    # Convert specified columns to integer type
    listings['duration_(secs)'] = listings['duration_(secs)'].astype(int, errors='ignore')
    listings['age'] = listings['age'].astype(int, errors='ignore')
    listings['sales'] = listings['sales'].astype(int, errors='ignore')
    listings['returned_amount'] = listings['returned_amount'].astype(int, errors='ignore')

    # Get the Airflow database URL from the configuration
    airflow_db_url = conf.get('core', 'sql_alchemy_conn')
    engine = create_engine(airflow_db_url, connect_args={'check_same_thread': False})  # Add connect_args for SQLite

    # Get a connection from the engine
    conn = engine.raw_connection()

    # Save the DataFrame to the database using the connection
    listings.to_sql('web_logs_cleans', conn, if_exists='replace', index=False)

    return "File processed and data saved to airflow.db"


# Define the task to process the CSV file
process_csv_task = PythonOperator(
    task_id='process_csv_file',
    python_callable=process_csv_file,
    op_args=[dag.dag_id],  # Pass the DAG ID as an argument to the function
    dag=dag,
)

process_csv_task






