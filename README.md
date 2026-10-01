# ?? AI Database Query Explainer & Optimizer

[![Django](https://img.shields.io/badge/Django-6.1-green.svg)](https://www.djangoproject.com/)
[![SQLite](https://img.shields.io/badge/SQLite-128k%2B%20Records-blue.svg)](https://www.sqlite.org/)
[![Groq AI](https://img.shields.io/badge/Groq%20AI-Llama%20%26%20GPT--OSS-orange.svg)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An enterprise-grade, AI-powered Database Query Assistant built with **Django**, **Groq AI (Llama 3.3 70B & GPT-OSS)**, and **SQLite**. It translates natural language into optimized SQL queries, provides line-by-line query explanations, suggests indexing optimizations, executes queries with sub-millisecond speeds over **128,000+ records**, and generates interactive visual analytics.

---

## ?? Key Features

- ??? **Natural Language to SQL**: Converts everyday human questions into precise, multi-table SQL queries with JOINs and aggregate functions.
- ?? **Line-by-Line Query Explainer**: Breaks down complex SQL statements clause-by-clause with plain-English technical explanations.
- ? **SQL Performance Optimizer**: Analyzes queries, provides a performance score (0–100), detects full table scans, and recommends B-Tree indexes.
- ?? **128,000+ Records Enterprise Database**: Pre-seeded SQLite database with indexed tables (`customers`, `products`, `employees`, `orders`, `order_items`).
- ?? **Interactive Query Runner Console**: Paginated SQL execution with sub-second response times and one-click **CSV** / **Excel (.xlsx)** exports.
- ?? **Dynamic Visual Analytics**: Auto-generates charts (Bar, Line, Pie, Doughnut) with data trend insights powered by Chart.js.
- ?? **Schema Explorer**: Real-time schema inspector displaying table structures, foreign key relationships, and row counts.
- ??? **Security Guardrails**: Read-only query enforcement, SQL injection sanitization, and query history auditing.

---

## ?? How to Run & Visit the Website

### 1. Clone the Repository
```bash
git clone https://github.com/bhavanasbhavanas416-rgb/AI-Database-Query-Explainer.git
cd AI-Database-Query-Explainer
```

### 2. Set Up Python Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory (or copy from `.env.example`):
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=*
GROQ_API_KEY=your-groq-api-key-here
PORT=8000
```
*(Note: If no Groq API Key is supplied, the application automatically uses its built-in Intelligent Schema-Aware Rule Engine!)*

### 5. Run Database Migrations & Seed Data
```bash
python manage.py migrate
python seed_large_db.py
```

### 6. Start the Development Server
```bash
python manage.py runserver
```

### 7. Visit the Website
Open your web browser and navigate to:
- ?? **Web Application**: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** (or `http://localhost:8000/`)
- ?? **Django Admin Portal**: **[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)**
  - **Username**: `admin`
  - **Password**: `admin123`

---

## ??? Database Structure (128,000+ Records)

The project includes pre-indexed SQLite datasets accessible in the app and in **DB Browser for SQLite**:

| Table | Records | Key Columns |
| :--- | :--- | :--- |
| **`customers`** | **15,000** | `customer_id`, `first_name`, `last_name`, `email`, `city`, `country`, `customer_segment`, `credit_limit` |
| **`products`** | **2,000** | `product_id`, `product_name`, `category`, `price`, `stock_quantity`, `supplier_name`, `rating` |
| **`employees`** | **1,000** | `employee_id`, `first_name`, `last_name`, `department`, `job_title`, `salary`, `hire_date` |
| **`orders`** | **45,000** | `order_id`, `customer_id`, `order_date`, `order_status`, `payment_method`, `total_amount` |
| **`order_items`** | **65,000** | `item_id`, `order_id`, `product_id`, `quantity`, `unit_price`, `discount_amount` |

### Opening in DB Browser for SQLite:
1. Open **DB Browser for SQLite**.
2. Click **Open Database** (`Ctrl + O`).
3. Select `db.sqlite3` or `data/enterprise_sample_100k.db`.
4. Navigate to the **Browse Data** tab and choose any table from the dropdown.

---

## ??? Technology Stack

- **Backend**: Python 3.12, Django 6.1, Django REST Framework
- **Database**: SQLite 3 with B-Tree Indexing (supports PostgreSQL & MySQL connections)
- **AI / LLM Integration**: Groq API (`openai/gpt-oss-120b`, `llama-3.3-70b-versatile`, `qwen/qwen3.8-27b`)
- **Frontend**: Glassmorphic HTML5 / Vanilla CSS3 / JavaScript (SPA Engine)
- **Data Export & Analytics**: `openpyxl`, `Chart.js`, `sqlparse`

---

## ?? License
This project is open source and available under the [MIT License](LICENSE).
