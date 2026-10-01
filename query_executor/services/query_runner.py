import time
import csv
import openpyxl
import re
import sqlparse
from io import StringIO, BytesIO
from database_manager.services.schema_inspector import get_connection_cursor

def execute_sql_safely(sql_query, db_conn_obj=None, page=1, page_size=50, allow_write=False):
    """
    Executes a SQL query safely against the active connection.
    Enforces security checks, records execution timing, formats tabular results, and provides pagination.
    """
    cleaned_sql = sql_query.strip().strip(';')
    sql_upper = cleaned_sql.upper()

    statements = [statement for statement in sqlparse.parse(cleaned_sql) if str(statement).strip()]
    if len(statements) != 1:
        raise PermissionError("Security Alert: Only one SQL statement can be executed at a time.")

    conn, cursor, engine = get_connection_cursor(db_conn_obj)

    if not allow_write:
        statement_type = statements[0].get_type()
        normalized_sql = sqlparse.format(cleaned_sql, strip_comments=True).lstrip()
        first_keyword = re.match(r"[A-Za-z]+", normalized_sql)
        keyword = first_keyword.group(0).upper() if first_keyword else ""
        explain_select = keyword == "EXPLAIN" and re.match(
            r"EXPLAIN(?:\s+(?:QUERY\s+PLAN|ANALYZE|VERBOSE))*(?:\s*\([^)]*\))?\s+SELECT\b",
            normalized_sql,
            re.IGNORECASE,
        )
        allowed_read = statement_type == "SELECT" or explain_select
        allowed_read = allowed_read or (engine != "sqlite" and keyword in ("SHOW", "DESCRIBE"))
        if not allowed_read:
            conn.close()
            raise PermissionError("Security Alert: Only read-only SQL queries are allowed.")

        if engine == "sqlite":
            conn.execute("PRAGMA query_only = ON")

    if page < 1 or page_size < 1:
        conn.close()
        raise ValueError("Page and page size must be positive integers.")

    start_time = time.time()
    columns = []
    rows = []
    total_rows = 0

    try:
        cursor.execute(cleaned_sql)
        
        # Check if query returns rows (e.g. SELECT, EXPLAIN, SHOW)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            raw_rows = cursor.fetchall()
            total_rows = len(raw_rows)

            # Paginate results
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_data = raw_rows[start_idx:end_idx]

            # Format rows into lists/dicts
            for r in page_data:
                if isinstance(r, dict):
                    rows.append([r[col] for col in columns])
                elif hasattr(r, 'keys'):
                    rows.append([r[col] for col in columns])
                else:
                    rows.append(list(r))
        else:
            conn.commit()
            columns = ["Result"]
            rows = [[f"Query executed successfully. {cursor.rowcount} row(s) affected."]]
            total_rows = cursor.rowcount

        execution_time_ms = round((time.time() - start_time) * 1000, 2)

    except Exception as e:
        conn.close()
        raise Exception(f"SQL Execution Error: {str(e)}")

    conn.close()

    total_pages = max(1, (total_rows + page_size - 1) // page_size)

    return {
        "sql": cleaned_sql + ";",
        "columns": columns,
        "rows": rows,
        "total_rows": total_rows,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "execution_time_ms": execution_time_ms
    }


def export_query_results_csv(columns, rows):
    """Generates CSV bytes buffer for query results download."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    for r in rows:
        writer.writerow(r)
    return output.getvalue().encode('utf-8')


def export_query_results_excel(columns, rows):
    """Generates Excel (.xlsx) bytes buffer for query results download using openpyxl."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Query Results"

    ws.append(columns)
    for r in rows:
        ws.append([str(val) if val is not None else "" for val in r])

    output = BytesIO()
    wb.save(output)
    return output.getvalue()
