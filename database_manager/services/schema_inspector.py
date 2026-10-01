import sqlite3
import os
from django.conf import settings

def get_connection_cursor(db_conn_obj):
    """
    Returns (connection, cursor, engine_type) for the given DatabaseConnection model instance.
    Defaults to db.sqlite3 / enterprise_sample_100k.db if active connection is not set or set to default sample.
    """
    if not db_conn_obj or db_conn_obj.is_default_sample or db_conn_obj.engine == 'sqlite':
        db_path = getattr(db_conn_obj, 'sqlite_file_path', None) if db_conn_obj else None
        if not db_path or not os.path.exists(db_path):
            db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
            if not os.path.exists(db_path):
                db_path = os.path.join(settings.BASE_DIR, 'data', 'enterprise_sample_100k.db')
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn, conn.cursor(), 'sqlite'

    elif db_conn_obj.engine == 'postgresql':
        try:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(
                dbname=db_conn_obj.db_name,
                user=db_conn_obj.username,
                password=db_conn_obj.password,
                host=db_conn_obj.host or 'localhost',
                port=db_conn_obj.port or 5432
            )
            return conn, conn.cursor(cursor_factory=psycopg2.extras.DictCursor), 'postgresql'
        except Exception as e:
            raise Exception(f"PostgreSQL Connection Error: {str(e)}")

    elif db_conn_obj.engine == 'mysql':
        try:
            import pymysql
            conn = pymysql.connect(
                db=db_conn_obj.db_name,
                user=db_conn_obj.username,
                password=db_conn_obj.password,
                host=db_conn_obj.host or 'localhost',
                port=db_conn_obj.port or 3306,
                cursorclass=pymysql.cursors.DictCursor
            )
            return conn, conn.cursor(), 'mysql'
        except Exception as e:
            raise Exception(f"MySQL Connection Error: {str(e)}")

    raise Exception(f"Unsupported database engine: {db_conn_obj.engine}")


def quote_identifier(identifier, engine):
    """Returns properly quoted table or column name depending on database engine."""
    if engine == 'mysql':
        return f"`{identifier}`"
    return f'"{identifier}"'

def extract_database_schema(db_conn_obj=None):
    """
    Extracts complete schema metadata for all tables matching DB Browser.
    """
    conn, cursor, engine = get_connection_cursor(db_conn_obj)
    tables_info = []
    relationships = []
    total_database_records = 0

    try:
        if engine == 'sqlite':
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY 
                  CASE 
                    WHEN name IN ('customers', 'products', 'employees', 'orders', 'order_items') THEN 0 
                    ELSE 1 
                  END, name;
            """)
            tables = [row['name'] if isinstance(row, dict) or hasattr(row, 'keys') else row[0] for row in cursor.fetchall()]

            for tbl in tables:
                q_tbl = quote_identifier(tbl, engine)
                try:
                    cursor.execute(f"SELECT COUNT(*) as cnt FROM {q_tbl}")
                    row_cnt_row = cursor.fetchone()
                    cnt = row_cnt_row['cnt'] if isinstance(row_cnt_row, dict) or hasattr(row_cnt_row, 'keys') else row_cnt_row[0]
                except Exception:
                    cnt = 0
                total_database_records += cnt

                cursor.execute(f"PRAGMA table_info({q_tbl})")
                cols = cursor.fetchall()
                columns_list = []
                for c in cols:
                    c_name = c['name'] if isinstance(c, dict) or hasattr(c, 'keys') else c[1]
                    c_type = c['type'] if isinstance(c, dict) or hasattr(c, 'keys') else c[2]
                    c_notnull = c['notnull'] if isinstance(c, dict) or hasattr(c, 'keys') else c[3]
                    c_pk = c['pk'] if isinstance(c, dict) or hasattr(c, 'keys') else c[5]
                    
                    columns_list.append({
                        "name": c_name,
                        "type": c_type or "TEXT",
                        "primary_key": bool(c_pk),
                        "nullable": not bool(c_notnull)
                    })

                cursor.execute(f"PRAGMA foreign_key_list({q_tbl})")
                fks = cursor.fetchall()
                for fk in fks:
                    from_col = fk['from'] if isinstance(fk, dict) or hasattr(fk, 'keys') else fk[3]
                    to_table = fk['table'] if isinstance(fk, dict) or hasattr(fk, 'keys') else fk[2]
                    to_col = fk['to'] if isinstance(fk, dict) or hasattr(fk, 'keys') else fk[4]
                    relationships.append({
                        "from_table": tbl,
                        "from_column": from_col,
                        "to_table": to_table,
                        "to_column": to_col
                    })

                tables_info.append({
                    "table_name": tbl,
                    "row_count": cnt,
                    "columns": columns_list
                })

        elif engine in ('postgresql', 'mysql'):
            query_tables = "SELECT table_name FROM information_schema.tables WHERE table_schema='public' OR table_schema=DATABASE();"
            cursor.execute(query_tables)
            tables = [r[0] for r in cursor.fetchall()]

            for tbl in tables:
                q_tbl = quote_identifier(tbl, engine)
                cursor.execute(f"SELECT COUNT(*) FROM {q_tbl}")
                cnt = cursor.fetchone()[0]
                total_database_records += cnt

                cursor.execute(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='{tbl}';")
                cols = cursor.fetchall()
                columns_list = []
                for c in cols:
                    columns_list.append({
                        "name": c[0],
                        "type": c[1],
                        "primary_key": 'id' in c[0].lower() or 'pk' in c[0].lower(),
                        "nullable": c[2] == 'YES'
                    })
                tables_info.append({
                    "table_name": tbl,
                    "row_count": cnt,
                    "columns": columns_list
                })

    finally:
        conn.close()

    return {
        "engine": engine,
        "total_tables": len(tables_info),
        "total_records": total_database_records,
        "tables": tables_info,
        "relationships": relationships
    }


def format_schema_for_ai_prompt(schema_data):
    """
    Formats the database schema into a compact text block for the AI model prompt.
    Focuses on primary business tables.
    """
    lines = [f"DATABASE SCHEMA METADATA (Total Tables: {schema_data['total_tables']}, Total Database Records: {schema_data['total_records']:,}):\n"]
    
    for tbl in schema_data['tables']:
        cols_str = ", ".join([f"{c['name']} ({c['type']}{' PK' if c['primary_key'] else ''})" for c in tbl['columns']])
        lines.append(f"Table: {tbl['table_name']} | Records: {tbl['row_count']:,}")
        lines.append(f"  Columns: {cols_str}\n")
    
    if schema_data['relationships']:
        lines.append("RELATIONSHIPS:")
        for rel in schema_data['relationships']:
            lines.append(f"  - {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}")
    
    return "\n".join(lines)
