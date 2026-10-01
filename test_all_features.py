import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from database_manager.models import DatabaseConnection
from authentication.models import UserProfile
from database_manager.services.schema_inspector import extract_database_schema

def test_full_application():
    print("==================================================")
    print("RUNNING END-TO-END VERIFICATION TEST SUITE...")
    print("==================================================")

    client = Client()

    # 1. Test Dashboard Home HTML View
    res = client.get('/')
    assert res.status_code == 200, f"Dashboard view failed with status {res.status_code}"
    print("[PASS] Dashboard Home View (HTTP 200 OK)")

    # 2. Test DB Connections API
    res = client.get('/api/v1/connections/')
    assert res.status_code == 200, f"Connections API failed with status {res.status_code}"
    data = res.json()
    assert 'connections' in data, "Connections API missing 'connections' key"
    print(f"[PASS] Connections API (HTTP 200 OK) - Found {len(data['connections'])} connection(s)")

    # 3. Test Schema Explorer API on 100,000+ Record Database
    res = client.get('/api/v1/schema/')
    assert res.status_code == 200, f"Schema API failed with status {res.status_code}"
    schema = res.json()
    print(f"[PASS] Schema Explorer API (HTTP 200 OK) - {schema['total_tables']} Tables, {schema['total_records']:,} Records inspected!")
    assert schema['total_records'] >= 100000, f"Expected >100,000 records, found {schema['total_records']}"

    # 4. Test NL to SQL AI Generation
    prompt = "Show top 10 customers by sales"
    res = client.post('/api/v1/query/generate/', data=json.dumps({'prompt': prompt}), content_type='application/json')
    assert res.status_code == 200, f"Generate SQL API failed with status {res.status_code}"
    gen_data = res.json()
    print(f"[PASS] NL to SQL Generator (HTTP 200 OK) - Prompt: '{prompt}' -> Generated SQL: {gen_data['generated_sql'].replace('\n', ' ')}")

    # 5. Test SQL Explainer API
    sql_to_explain = "SELECT department, COUNT(*) FROM employees GROUP BY department;"
    res = client.post('/api/v1/query/explain/', data=json.dumps({'sql': sql_to_explain}), content_type='application/json')
    assert res.status_code == 200, f"Explain SQL API failed with status {res.status_code}"
    exp_data = res.json()
    print(f"[PASS] Query Explainer API (HTTP 200 OK) - Purpose: {exp_data['purpose']}")

    # 6. Test Query Optimization Engine API
    sql_to_optimize = "SELECT * FROM orders WHERE customer_id = 500;"
    res = client.post('/api/v1/query/optimize/', data=json.dumps({'sql': sql_to_optimize}), content_type='application/json')
    assert res.status_code == 200, f"Optimize SQL API failed with status {res.status_code}"
    opt_data = res.json()
    print(f"[PASS] Query Optimization Engine (HTTP 200 OK) - Score: {opt_data['performance_score']}/100 | Suggestions: {len(opt_data['optimization_suggestions'])}")

    # 7. Test Safe SQL Execution Engine against 100,000+ Database
    sql_to_exec = gen_data['generated_sql']
    res = client.post('/api/v1/query/execute/', data=json.dumps({'sql': sql_to_exec}), content_type='application/json')
    assert res.status_code == 200, f"Execute SQL API failed with status {res.status_code}"
    exec_data = res.json()
    print(f"[PASS] Query Execution Engine (HTTP 200 OK) - Executed in {exec_data['execution_time_ms']} ms | Returned {exec_data['total_rows']} rows!")

    # 8. Test CSV & Excel Export APIs
    res_csv = client.post('/api/v1/export/csv/', data=json.dumps({'sql': sql_to_exec}), content_type='application/json')
    assert res_csv.status_code == 200 and res_csv['Content-Type'] == 'text/csv', "CSV export failed"
    print("[PASS] CSV Export Engine (HTTP 200 OK)")

    res_xlsx = client.post('/api/v1/export/excel/', data=json.dumps({'sql': sql_to_exec}), content_type='application/json')
    assert res_xlsx.status_code == 200, "Excel export failed"
    print("[PASS] Excel Export Engine (HTTP 200 OK)")

    # 9. Test Analytics Visualization API
    res_analytics = client.post('/api/v1/analytics/chart/', data=json.dumps({'sql': sql_to_exec, 'chart_type': 'bar'}), content_type='application/json')
    assert res_analytics.status_code == 200, "Analytics API failed"
    chart_data = res_analytics.json()
    print(f"[PASS] Database Analytics Engine (HTTP 200 OK) - Insights: {chart_data['insights']}")

    # 10. Test Query History API
    res_hist = client.get('/api/v1/query/history/')
    assert res_hist.status_code == 200, "History API failed"
    hist_data = res_hist.json()
    print(f"[PASS] Query History Audit Log (HTTP 200 OK) - Recorded {len(hist_data['history'])} log item(s)")

    # 11. Test Admin Panel Metrics API
    res_admin = client.get('/api/v1/admin/metrics/')
    assert res_admin.status_code == 200, "Admin Metrics API failed"
    admin_data = res_admin.json()
    print(f"[PASS] Admin Panel Metrics (HTTP 200 OK) - System Status: {admin_data['system_status']}")

    print("==================================================")
    print("ALL 11 TEST VERIFICATIONS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    test_full_application()
