import os
import pyodbc
import pandas as pd

def get_connection():
    db=os.getenv('STEEL_DB','SteelTransaction_POC')
    if db not in ('SteelTransaction_POC','SteelTransaction_PROD'): raise ValueError('Invalid database')
    return pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+os.environ['STEEL_SERVER']+';DATABASE='+db+';Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;',autocommit=False)

def read_data(sql):
    conn=get_connection()
    try: return pd.read_sql_query(sql,conn,coerce_float=False)
    finally: conn.close()
