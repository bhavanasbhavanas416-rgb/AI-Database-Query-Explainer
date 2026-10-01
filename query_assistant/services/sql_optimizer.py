import re

def analyze_and_optimize_sql(sql_query, schema_data=None):
    """
    Evaluates SQL query performance bottleneck, calculates score (0-100),
    generates index recommendations, complexity rating, and cost reduction tips.
    """
    score = 100
    suggestions = []
    index_recommendations = []
    cost_tips = []
    complexity = "Low"

    sql_upper = sql_query.upper()

    # Bottleneck 1: Check for SELECT *
    if "SELECT *" in sql_upper:
        score -= 20
        suggestions.append("Avoid 'SELECT *': Explicitly list required column names to reduce I/O bandwidth and RAM usage.")
        cost_tips.append("Replacing 'SELECT *' with targeted columns reduces data transfer size across network connections.")

    # Bottleneck 2: Check for missing LIMIT on large datasets
    if "LIMIT" not in sql_upper and ("SELECT" in sql_upper and "COUNT(" not in sql_upper):
        score -= 15
        suggestions.append("Add a 'LIMIT' clause: Restrict returned record count to prevent full table scans on large tables (100,000+ records).")
        cost_tips.append("Adding a LIMIT clause stops execution early once enough rows are fetched.")

    # Bottleneck 3: Implicit CROSS JOIN check (commas in FROM)
    from_match = re.search(r'FROM\s+([a-zA-Z0-9_,\s]+)(WHERE|GROUP|ORDER|LIMIT|$)', sql_upper)
    if from_match and ',' in from_match.group(1):
        score -= 25
        complexity = "High"
        suggestions.append("Replace implicit Cartesian cross join (comma in FROM clause) with explicit ANSI 'JOIN ... ON ...' syntax.")
        cost_tips.append("Implicit cross joins create exponential row multiplication before filtering.")

    # Bottleneck 4: Check JOIN columns without indexes
    tables_in_query = []
    if schema_data and "tables" in schema_data:
        for tbl in schema_data["tables"]:
            tname = tbl["table_name"]
            if re.search(r'\b' + re.escape(tname) + r'\b', sql_query, re.IGNORECASE):
                tables_in_query.append(tbl)

    # Generate smart index recommendations for WHERE and JOIN columns
    where_match = re.search(r'WHERE\s+(.*?)(GROUP|ORDER|LIMIT|$)', sql_query, re.IGNORECASE | re.DOTALL)
    if where_match:
        where_clause = where_match.group(1)
        for tbl in tables_in_query:
            tname = tbl["table_name"]
            for col in tbl["columns"]:
                col_name = col["name"]
                if not col["primary_key"] and re.search(r'\b' + re.escape(col_name) + r'\b', where_clause, re.IGNORECASE):
                    idx_stmt = f"CREATE INDEX IF NOT EXISTS idx_{tname}_{col_name} ON {tname}({col_name});"
                    if idx_stmt not in index_recommendations:
                        index_recommendations.append(idx_stmt)

    join_matches = re.findall(r'ON\s+([a-zA-Z0-9_\.]+)\s*=\s*([a-zA-Z0-9_\.]+)', sql_query, re.IGNORECASE)
    for m in join_matches:
        for side in m:
            parts = side.split('.')
            if len(parts) == 2:
                tbl_part, col_part = parts[0], parts[1]
                idx_stmt = f"CREATE INDEX IF NOT EXISTS idx_{tbl_part}_{col_part} ON {tbl_part}({col_part});"
                if idx_stmt not in index_recommendations:
                    index_recommendations.append(idx_stmt)

    # Bottleneck 5: Functions in WHERE clause (e.g. LOWER(col) = ...)
    if re.search(r'WHERE\s+.*\b(LOWER|UPPER|SUBSTR|DATE)\(', sql_upper):
        score -= 15
        suggestions.append("Avoid wrapping columns in scalar functions inside WHERE conditions as it prevents index utilization.")
        cost_tips.append("Use functional indexes or exact column comparisons.")

    # Compute overall complexity
    join_count = sql_upper.count("JOIN")
    subquery_count = sql_upper.count("SELECT") - 1
    if join_count >= 3 or subquery_count >= 2:
        complexity = "High"
    elif join_count >= 1 or "GROUP BY" in sql_upper:
        complexity = "Medium"

    # Default positive suggestions if query is already clean
    if score >= 90:
        suggestions.append("Query follows modern SQL best practices! Column selection, indexing, and filtering are well structured.")
        cost_tips.append("Optimal execution plan anticipated.")

    score = max(30, min(100, score))

    return {
        "performance_score": score,
        "optimization_suggestions": suggestions,
        "index_recommendations": index_recommendations,
        "query_complexity": complexity,
        "cost_reduction_tips": cost_tips
    }
