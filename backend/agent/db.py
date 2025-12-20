"""
Database connection utilities for the agent.
"""
import os
import psycopg2
from psycopg2 import pool
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

_connection_pool: Optional[pool.ThreadedConnectionPool] = None

def get_db_connection():
    global _connection_pool
    
    if _connection_pool is None:
        try:
            _connection_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=5,
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", "chat_to_purchase"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres"),
            )
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise
    
    return _connection_pool.getconn()


def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        row_dict = {}
        for i, col in enumerate(columns):
            value = row[i]
            if isinstance(value, (int, float)) or hasattr(value, '__float__'):
                row_dict[col] = float(value)
            else:
                row_dict[col] = value
        results.append(row_dict)
    
    cursor.close()
    _connection_pool.putconn(conn)
    return results

