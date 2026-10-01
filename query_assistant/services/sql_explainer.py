import re
import sqlparse

def explain_sql_query(sql_query, schema_data=None):
    """
    Parses and explains a SQL query into structured components:
    - Purpose Summary
    - Tables Used
    - SQL Operations Breakdown
    - Line-by-Line Breakdown
    - Clause Analysis (SELECT, WHERE, JOIN, GROUP BY, ORDER BY, LIMIT)
    - Technical Description
    """
    cleaned_sql = sql_query.strip()

    # Extract tables used
    known_tables = []
    if schema_data and "tables" in schema_data:
        known_tables = [t["table_name"] for t in schema_data["tables"]]
    
    tables_used = []
    for tbl in known_tables:
        if re.search(r'\b' + re.escape(tbl) + r'\b', cleaned_sql, re.IGNORECASE):
            tables_used.append(tbl)
    
    if not tables_used:
        # Fallback regex search for FROM/JOIN
        matches = re.findall(r'(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)', cleaned_sql, re.IGNORECASE)
        tables_used = list(set(matches))

    # Detect SQL Operations & Keywords
    keywords = ["SELECT", "FROM", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT", "COUNT", "SUM", "AVG", "MAX", "MIN", "DISTINCT"]
    operations_found = []
    for kw in keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', cleaned_sql, re.IGNORECASE):
            operations_found.append(kw)

    # Line-by-Line Breakdown
    lines = [l.strip() for l in cleaned_sql.split('\n') if l.strip()]
    line_by_line = []

    for idx, line in enumerate(lines, 1):
        line_upper = line.upper()
        explanation_text = "Executes statement component."
        
        if line_upper.startswith("SELECT"):
            if "*" in line:
                explanation_text = "Retrieves all available columns from the specified dataset."
            elif any(agg in line_upper for agg in ["COUNT", "SUM", "AVG", "MAX", "MIN"]):
                explanation_text = "Calculates aggregate functions (such as counts, sums, or averages) across records."
            else:
                explanation_text = f"Selects specific fields ({line.replace('SELECT', '').strip()}) to include in the query result."

        elif line_upper.startswith("FROM"):
            explanation_text = f"Specifies the primary source table ({line.replace('FROM', '').strip()}) to read data from."

        elif "JOIN" in line_upper:
            explanation_text = "Combines rows from multiple tables based on a related matching key column."

        elif line_upper.startswith("WHERE"):
            explanation_text = "Filters input rows based on specified logical condition(s) before grouping or output."

        elif line_upper.startswith("GROUP BY"):
            explanation_text = "Aggregates rows sharing common values in the specified column(s) into summary groups."

        elif line_upper.startswith("HAVING"):
            explanation_text = "Filters aggregated group results created by the GROUP BY clause."

        elif line_upper.startswith("ORDER BY"):
            direction = "descending (highest to lowest)" if "DESC" in line_upper else "ascending (lowest to highest)"
            explanation_text = f"Sorts the final query result set in {direction} order."

        elif line_upper.startswith("LIMIT"):
            num = re.search(r'\d+', line)
            limit_n = num.group(0) if num else "specified"
            explanation_text = f"Restricts the output set to maximum {limit_n} rows for efficient viewing."

        line_by_line.append({
            "line_number": idx,
            "code": line,
            "explanation": explanation_text
        })

    # Purpose summary generator
    tbl_str = ", ".join(tables_used) if tables_used else "the database tables"
    purpose = f"Retrieves and analyzes data from {tbl_str}"
    if "GROUP BY" in cleaned_sql.upper():
        purpose += " summarized by grouping categories"
    if "ORDER BY" in cleaned_sql.upper():
        purpose += " sorted in order"
    if "LIMIT" in cleaned_sql.upper():
        purpose += " with restricted row output"
    purpose += "."

    # Clause breakdown map
    clause_breakdown = {}
    clauses = ["SELECT", "FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT"]
    for c in clauses:
        pattern = r'\b' + c + r'\b(.*?)(?=\b(?:SELECT|FROM|WHERE|GROUP BY|HAVING|ORDER BY|LIMIT)\b|$)'
        m = re.search(pattern, cleaned_sql, re.IGNORECASE | re.DOTALL)
        if m:
            clause_breakdown[c] = m.group(1).strip()

    technical_description = (
        f"This query targets table(s) [{', '.join(tables_used)}]. It uses {', '.join(operations_found)} "
        f"to process structural data and return formatted results efficiently."
    )

    return {
        "purpose": purpose,
        "tables_used": tables_used,
        "sql_operations": operations_found,
        "line_by_line": line_by_line,
        "clause_breakdown": clause_breakdown,
        "technical_description": technical_description
    }
