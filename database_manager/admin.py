from django.contrib import admin
from .models import DatabaseConnection, Customer, Product, Employee, Order, OrderItem

@admin.register(DatabaseConnection)
class DatabaseConnectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'engine', 'host', 'port', 'db_name', 'is_active', 'is_default_sample', 'created_at')
    list_filter = ('engine', 'is_active', 'is_default_sample')
    search_fields = ('name', 'db_name', 'host')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'first_name', 'last_name', 'email', 'city', 'country', 'customer_segment', 'credit_limit')
    search_fields = ('first_name', 'last_name', 'email', 'city', 'country')
    list_filter = ('customer_segment', 'country')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'product_name', 'category', 'price', 'stock_quantity', 'supplier_name', 'rating')
    search_fields = ('product_name', 'category', 'supplier_name')
    list_filter = ('category', 'rating')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'department', 'job_title', 'salary', 'hire_date')
    search_fields = ('first_name', 'last_name', 'department', 'job_title')
    list_filter = ('department', 'job_title')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer', 'order_date', 'order_status', 'payment_method', 'total_amount')
    search_fields = ('order_id', 'customer__first_name', 'customer__last_name', 'customer__email')
    list_filter = ('order_status', 'payment_method')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'order', 'product', 'quantity', 'unit_price', 'discount_amount')
    search_fields = ('item_id', 'order__order_id', 'product__product_name')
