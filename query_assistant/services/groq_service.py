import os
import json
import re
from dotenv import load_dotenv
from groq import Groq
from database_manager.services.schema_inspector import extract_database_schema, format_schema_for_ai_prompt
from .sql_explainer import explain_sql_query
from .sql_optimizer import analyze_and_optimize_sql

load_dotenv()

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"

def generate_sql_from_nl(user_prompt, user_profile=None, db_connection=None):
    """
    Generates SQL query from Natural Language using Groq API (openai/gpt-oss-120b) or Fallback Engine.
    Employs schema awareness without sending whole database payloads.
    """
    schema_data = extract_database_schema(db_connection)
    schema_prompt = format_schema_for_ai_prompt(schema_data)

    # Check for Groq API Key (from profile, env, or request)
    api_key = None
    if user_profile and user_profile.groq_api_key:
        api_key = user_profile.groq_api_key
    elif os.getenv("GROQ_API_KEY"):
        api_key = os.getenv("GROQ_API_KEY")

    sql_query = None
    ai_raw_response = None
    groq_success = False

    if api_key:
        for model_candidate in [DEFAULT_GROQ_MODEL, "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]:
            try:
                client = Groq(api_key=api_key.strip())
                system_instruction = (
                    "You are an expert SQL DBA and AI Database Assistant specializing in generating optimal SQL queries "
                    "from natural language prompts based strictly on the provided database schema.\n"
                    "RULES:\n"
                    "1. Return ONLY valid SQL query code inside ```sql ``` markdown blocks.\n"
                    "2. Use table names and column names strictly as defined in the schema.\n"
                    "3. Perform correct JOINs when multi-table queries are needed.\n"
                    "4. Apply aggregate functions (COUNT, SUM, AVG, MAX, MIN) and GROUP BY where appropriate.\n"
                    "5. Do NOT modify data (no DROP, DELETE, INSERT, UPDATE, TRUNCATE) unless explicitly asked.\n\n"
                    f"{schema_prompt}"
                )

                completion = client.chat.completions.create(
                    model=model_candidate,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=800
                )

                ai_raw_response = completion.choices[0].message.content
                match = re.search(r"```sql\s*(.*?)\s*```", ai_raw_response, re.DOTALL | re.IGNORECASE)
                if match:
                    sql_query = match.group(1).strip()
                else:
                    sql_query = ai_raw_response.strip().strip(';').strip() + ';'
                groq_success = True
                break
            except Exception as e:
                print(f"Groq API call notice ({model_candidate}): {str(e)}.")

    # Fallback / Smart Local Schema Engine if API Key isn't provided or fails
    if not sql_query:
        sql_query = smart_local_sql_generator(user_prompt, schema_data)

    sql_query = sql_query.strip()
    if not sql_query.endswith(';'):
        sql_query += ';'

    explanation = explain_sql_query(sql_query, schema_data)
    optimization = analyze_and_optimize_sql(sql_query, schema_data)

    return {
        "user_prompt": user_prompt,
        "generated_sql": sql_query,
        "explanation": explanation,
        "optimization": optimization,
        "model_used": DEFAULT_GROQ_MODEL if groq_success else "Schema-Aware Rule Engine (Fallback)"
    }


def smart_local_sql_generator(prompt, schema_data):
    """
    Local Intelligent Schema-Aware SQL Rule Engine when Groq API key is not present.
    Supports multi-table queries, aggregates, sorting, filtering, and joins.
    """
    prompt_lower = prompt.lower()
    table_names = [t["table_name"] for t in schema_data.get("tables", [])]

    if "customer" in prompt_lower and ("sales" in prompt_lower or "spent" in prompt_lower or "order" in prompt_lower or "top" in prompt_lower):
        limit_match = re.search(r"\btop\s*(\d+)", prompt_lower)
        limit_val = limit_match.group(1) if limit_match else "10"
        return f"SELECT c.customer_id, c.first_name, c.last_name, c.email, COUNT(o.order_id) AS total_orders, ROUND(SUM(o.total_amount), 2) AS total_spent\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nGROUP BY c.customer_id, c.first_name, c.last_name, c.email\nORDER BY total_spent DESC\nLIMIT {limit_val};"

    if "employee" in prompt_lower and "department" in prompt_lower:
        return "SELECT department, COUNT(*) AS employee_count, ROUND(AVG(salary), 2) AS average_salary\nFROM employees\nGROUP BY department\nORDER BY employee_count DESC;"

    if "product" in prompt_lower or "item" in prompt_lower:
        if "category" in prompt_lower:
            return "SELECT category, COUNT(*) AS product_count, ROUND(AVG(price), 2) AS avg_price, SUM(stock_quantity) AS total_stock\nFROM products\nGROUP BY category\nORDER BY total_stock DESC;"
        elif "top" in prompt_lower or "rating" in prompt_lower or "expensive" in prompt_lower:
            return "SELECT product_name, category, price, stock_quantity, rating\nFROM products\nORDER BY rating DESC, price DESC\nLIMIT 10;"

    if "order" in prompt_lower and ("status" in prompt_lower or "payment" in prompt_lower):
        return "SELECT order_status, payment_method, COUNT(*) AS total_orders, ROUND(SUM(total_amount), 2) AS total_revenue\nFROM orders\nGROUP BY order_status, payment_method\nORDER BY total_revenue DESC;"

    target_table = None
    for tbl in table_names:
        if tbl.rstrip('s') in prompt_lower or tbl in prompt_lower:
            target_table = tbl
            break

    if not target_table:
        target_table = table_names[0] if table_names else "customers"

    limit_match = re.search(r"\b(limit|top)\s*(\d+)", prompt_lower)
    limit_clause = f" LIMIT {limit_match.group(2)}" if limit_match else " LIMIT 10"

    return f"SELECT *\nFROM {target_table}\nORDER BY 1 DESC{limit_clause};"
