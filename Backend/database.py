# database.py
import psycopg2
from psycopg2 import sql

def get_connection():
    return psycopg2.connect(
        dbname="swingbell",
        user="asimith",
        password="asimith",
        host="13.126.33.160",
        port="5432"
    )
