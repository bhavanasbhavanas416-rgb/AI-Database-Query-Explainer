import os
import sqlite3
import random
import time
from datetime import datetime, timedelta

def seed_enterprise_db(db_path):
    print(f"Creating sample enterprise database at {db_path}...")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fast bulk insertion mode
    cursor.execute("PRAGMA synchronous = OFF;")
    cursor.execute("PRAGMA journal_mode = MEMORY;")

    # 1. Create Tables
    print("Creating table schemas...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        city TEXT,
        country TEXT,
        customer_segment TEXT,
        credit_limit REAL,
        registration_date DATE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock_quantity INTEGER NOT NULL,
        supplier_name TEXT,
        rating REAL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        department TEXT NOT NULL,
        job_title TEXT NOT NULL,
        salary REAL NOT NULL,
        hire_date DATE,
        manager_id INTEGER
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        order_date DATE NOT NULL,
        order_status TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        shipping_cost REAL,
        total_amount REAL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        discount_amount REAL DEFAULT 0,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)

    # Seed Constants
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Rahul", "Priya", "Amit", "Ananya", "Alex", "Sophia", "Liam", "Emma", "Noah", "Olivia"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Sharma", "Verma", "Patel", "Chen", "Kim"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "London", "Toronto", "Sydney", "Mumbai", "Tokyo", "Paris", "Berlin", "Singapore", "San Francisco", "Austin", "Seattle", "Chicago", "Boston"]
    countries = ["USA", "Canada", "UK", "Australia", "India", "Germany", "France", "Japan", "Singapore"]
    segments = ["Enterprise", "Small Business", "Retail Consumer", "VIP", "Government"]
    departments = ["Engineering", "Sales", "Marketing", "Customer Support", "Finance", "Human Resources", "Product", "Operations"]
    titles = ["Software Engineer", "Senior Architect", "Account Executive", "Marketing Manager", "Support Lead", "Financial Analyst", "HR Specialist", "Product Manager", "Operations Director"]

    categories = ["Electronics", "Computers", "Office Supplies", "Furniture", "Networking", "Software", "Mobile Devices", "Accessories"]
    statuses = ["Completed", "Pending", "Shipped", "Cancelled", "Processing"]
    payment_methods = ["Credit Card", "PayPal", "Bank Transfer", "Crypto", "Invoice"]

    start_time = time.time()

    # Seed Customers (15,000)
    print("Seeding 15,000 Customers...")
    customers_data = []
    base_date = datetime(2020, 1, 1)
    for i in range(1, 15001):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        email = f"{fname.lower()}.{lname.lower()}{i}@enterprise-example.com"
        city = random.choice(cities)
        country = random.choice(countries)
        segment = random.choice(segments)
        credit = round(random.uniform(1000, 50000), 2)
        reg_date = (base_date + timedelta(days=random.randint(0, 1800))).strftime("%Y-%m-%d")
        customers_data.append((fname, lname, email, city, country, segment, credit, reg_date))
    cursor.executemany("INSERT INTO customers (first_name, last_name, email, city, country, customer_segment, credit_limit, registration_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", customers_data)

    # Seed Products (2,000)
    print("Seeding 2,000 Products...")
    products_data = []
    for i in range(1, 2001):
        cat = random.choice(categories)
        pname = f"{cat} Pro Series {i}"
        price = round(random.uniform(10, 2500), 2)
        stock = random.randint(5, 1000)
        supplier = f"TechCorp Global {random.randint(1, 20)}"
        rating = round(random.uniform(3.0, 5.0), 1)
        products_data.append((pname, cat, price, stock, supplier, rating))
    cursor.executemany("INSERT INTO products (product_name, category, price, stock_quantity, supplier_name, rating) VALUES (?, ?, ?, ?, ?, ?)", products_data)

    # Seed Employees (1,000)
    print("Seeding 1,000 Employees...")
    employees_data = []
    for i in range(1, 1001):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        dept = random.choice(departments)
        title = random.choice(titles)
        salary = round(random.uniform(45000, 180000), 2)
        hdate = (base_date + timedelta(days=random.randint(0, 2000))).strftime("%Y-%m-%d")
        mgr_id = random.randint(1, 50) if i > 50 else None
        employees_data.append((fname, lname, dept, title, salary, hdate, mgr_id))
    cursor.executemany("INSERT INTO employees (first_name, last_name, department, job_title, salary, hire_date, manager_id) VALUES (?, ?, ?, ?, ?, ?, ?)", employees_data)

    # Seed Orders (45,000)
    print("Seeding 45,000 Orders...")
    orders_data = []
    order_date_base = datetime(2022, 1, 1)
    for i in range(1, 45001):
        cust_id = random.randint(1, 15000)
        odate = (order_date_base + timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%d")
        status = random.choice(statuses)
        pmethod = random.choice(payment_methods)
        shipping = round(random.uniform(0, 50), 2)
        orders_data.append((cust_id, odate, status, pmethod, shipping, 0.0))
    cursor.executemany("INSERT INTO orders (customer_id, order_date, order_status, payment_method, shipping_cost, total_amount) VALUES (?, ?, ?, ?, ?, ?)", orders_data)

    # Seed Order Items (65,000)
    print("Seeding 65,000 Order Items...")
    items_data = []
    order_totals = {}
    for i in range(1, 65001):
        ord_id = random.randint(1, 45000)
        prod_id = random.randint(1, 2000)
        qty = random.randint(1, 5)
        price = round(random.uniform(20, 1500), 2)
        discount = round(random.uniform(0, price * 0.15), 2)
        item_total = (qty * price) - discount
        items_data.append((ord_id, prod_id, qty, price, discount))
        order_totals[ord_id] = order_totals.get(ord_id, 0.0) + item_total

    cursor.executemany("INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_amount) VALUES (?, ?, ?, ?, ?)", items_data)

    # Update total amounts in orders
    print("Updating Order totals...")
    update_totals = [(round(amt, 2), oid) for oid, amt in order_totals.items()]
    cursor.executemany("UPDATE orders SET total_amount = ? WHERE order_id = ?", update_totals)

    # Create Indexes for maximum performance
    print("Creating Indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_country ON customers(country);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);")

    conn.commit()
    conn.close()

    total_records = 15000 + 2000 + 1000 + 45000 + 65000
    elapsed = round(time.time() - start_time, 2)
    print(f"Success! Created {db_path} with {total_records:,} total records in {elapsed} seconds!")

if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(__file__), "data", "enterprise_sample_100k.db")
    seed_enterprise_db(db_file)
