from django.db import models
from django.contrib.auth.models import User

class DatabaseConnection(models.Model):
    ENGINE_CHOICES = (
        ('sqlite', 'SQLite'),
        ('postgresql', 'PostgreSQL'),
        ('mysql', 'MySQL'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections', null=True, blank=True)
    name = models.CharField(max_length=100)
    engine = models.CharField(max_length=20, choices=ENGINE_CHOICES, default='sqlite')
    host = models.CharField(max_length=255, blank=True, null=True, default='localhost')
    port = models.IntegerField(blank=True, null=True, default=5432)
    db_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    sqlite_file_path = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_default_sample = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.engine})"


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    customer_segment = models.CharField(max_length=100, blank=True, null=True)
    credit_limit = models.FloatField(blank=True, null=True)
    registration_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'customers'
        managed = False
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    price = models.FloatField()
    stock_quantity = models.IntegerField()
    supplier_name = models.CharField(max_length=255, blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'products'
        managed = False
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return f"{self.product_name} - ${self.price}"


class Employee(models.Model):
    employee_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    salary = models.FloatField()
    hire_date = models.DateField(blank=True, null=True)
    manager_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'employees'
        managed = False
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.job_title} - {self.department})"


class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, db_column='customer_id')
    order_date = models.DateField()
    order_status = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=50)
    shipping_cost = models.FloatField(blank=True, null=True)
    total_amount = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'orders'
        managed = False
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f"Order #{self.order_id} - {self.order_status} (${self.total_amount})"


class OrderItem(models.Model):
    item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.DO_NOTHING, db_column='order_id')
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, db_column='product_id')
    quantity = models.IntegerField()
    unit_price = models.FloatField()
    discount_amount = models.FloatField(default=0)

    class Meta:
        db_table = 'order_items'
        managed = False
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"Item #{self.item_id} (Order #{self.order_id}, Product #{self.product_id})"
