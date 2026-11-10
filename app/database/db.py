"""
Rydeon - MySQL Connection Pool and Database Handler
---------------------------------------------------
Provides connection pooling, transaction context managers, query helpers,
and schema initialization routines using mysql-connector-python.
"""

import os
from contextlib import contextmanager
import mysql.connector
from mysql.connector import errorcode, pooling
from flask import current_app

_connection_pool = None

def get_connection_pool(config=None):
    """Initializes or retrieves the singleton MySQLConnectionPool."""
    global _connection_pool
    if _connection_pool is None:
        if config is None:
            # Fallback to current_app.config or environment
            if current_app:
                cfg = current_app.config
                host = cfg.get('DB_HOST', 'localhost')
                port = cfg.get('DB_PORT', 3306)
                user = cfg.get('DB_USER', 'root')
                password = cfg.get('DB_PASSWORD', '')
                database = cfg.get('DB_NAME', 'vehicle_rental_system')
                pool_name = cfg.get('DB_POOL_NAME', 'rydeon_pool')
                pool_size = cfg.get('DB_POOL_SIZE', 5)
            else:
                host = os.environ.get('DB_HOST', 'localhost')
                port = int(os.environ.get('DB_PORT', 3306))
                user = os.environ.get('DB_USER', 'root')
                password = os.environ.get('DB_PASSWORD', '')
                database = os.environ.get('DB_NAME', 'vehicle_rental_system')
                pool_name = os.environ.get('DB_POOL_NAME', 'rydeon_pool')
                pool_size = int(os.environ.get('DB_POOL_SIZE', 5))
        else:
            host = config.get('DB_HOST', 'localhost')
            port = int(config.get('DB_PORT', 3306))
            user = config.get('DB_USER', 'root')
            password = config.get('DB_PASSWORD', '')
            database = config.get('DB_NAME', 'vehicle_rental_system')
            pool_name = config.get('DB_POOL_NAME', 'rydeon_pool')
            pool_size = int(config.get('DB_POOL_SIZE', 5))

        try:
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=pool_size,
                pool_reset_session=True,
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=False
            )
        except mysql.connector.Error as err:
            # If the database does not exist yet during initial boot, create pool without database
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                _connection_pool = pooling.MySQLConnectionPool(
                    pool_name=pool_name,
                    pool_size=pool_size,
                    pool_reset_session=True,
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    charset='utf8mb4',
                    collation='utf8mb4_unicode_ci',
                    autocommit=False
                )
            else:
                raise err
    return _connection_pool

def reset_connection_pool():
    """Resets the singleton connection pool (useful for tests and re-initialization)."""
    global _connection_pool
    _connection_pool = None

def get_raw_connection(config=None):
    """Direct non-pooled connection, useful for DDL migrations or initial DB creation."""
    if config is None and current_app:
        cfg = current_app.config
        return mysql.connector.connect(
            host=cfg.get('DB_HOST', 'localhost'),
            port=cfg.get('DB_PORT', 3306),
            user=cfg.get('DB_USER', 'root'),
            password=cfg.get('DB_PASSWORD', ''),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )

@contextmanager
def get_db_cursor(commit=False, dictionary=True):
    """
    Context manager yielding a database connection and cursor.
    Handles rollback on exceptions and returns the connection to the pool.
    """
    pool = get_connection_pool()
    conn = pool.get_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield conn, cursor
        if commit:
            conn.commit()
    except Exception as exc:
        conn.rollback()
        raise exc
    finally:
        cursor.close()
        conn.close()

def execute_query(sql, params=None, fetch_one=False, fetch_all=False, commit=False, dictionary=True):
    """
    Executes a parameterized SQL query safely.
    Uses %s placeholders to guarantee SQL injection prevention.
    """
    with get_db_cursor(commit=commit, dictionary=dictionary) as (conn, cursor):
        cursor.execute(sql, params or ())
        if commit:
            last_id = cursor.lastrowid
            row_count = cursor.rowcount
            return {'lastrowid': last_id, 'rowcount': row_count}
        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()
        return None

def check_db_health():
    """Health check ping returning (status_bool, detail_message)."""
    try:
        result = execute_query("SELECT 1 AS health_check", fetch_one=True)
        if result and result.get('health_check') == 1:
            return True, "Database connection operational."
        return False, "Health check query failed."
    except Exception as err:
        return False, f"Database connection error: {str(err)}"

def init_db(schema_path=None):
    """
    Initializes the MySQL database schema from schema.sql.
    Creates database and all required tables if they do not exist.
    """
    if schema_path is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        schema_path = os.path.join(base_dir, 'app', 'database', 'schema.sql')

    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Split commands by semicolon, ignoring empty lines/comments
    raw_conn = get_raw_connection()
    cursor = raw_conn.cursor()
    try:
        for statement in schema_sql.split(';'):
            clean_stmt = statement.strip()
            if clean_stmt:
                cursor.execute(clean_stmt)
        raw_conn.commit()
    finally:
        cursor.close()
        raw_conn.close()

    # Reset pool so it binds to the new database
    reset_connection_pool()
