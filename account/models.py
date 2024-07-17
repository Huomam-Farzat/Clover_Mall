from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
# Create your models here.
choices = {
    ## Clover Mall
    ("Food and Beverages","Food and Beverages"),
    ("Household Supplies","Household Supplies"),
    ("Health Beauty","Health Beauty"),
    ("Clothing Accessories","Clothing Accessories"),
    ("Electronics Appliances","Electronics Appliances"),
    ## stores in mall
    ("Savory Delight","Savory Delight"),
    ("Urban Bite","Urban Bite"),
    ("Trend Setters","Trend Setters"),
    ("Gourmet Corner","Gourmet Corner"),
    ("Tech World","Tech World")
    }

class CustomUser(AbstractUser):
    first_name= models.CharField(max_length=15,default="",blank=False)
    last_name= models.CharField(max_length=20,default="",blank=False)
    phone_number = models.CharField(max_length=10,default="",blank=False,unique=True,validators=[
        RegexValidator(regex=r'^09\d{8}$', message='Invalid phone number')])
    password= models.CharField(max_length=20,default="",blank=False)
    email = None

    USERNAME_FIELD = 'phone_number'
    # REQUIRED_FIELDS = ['username']
    def __str__(self) :
        return self.first_name


class Product(models.Model):
    name = models.CharField(max_length=200, default="", blank=False)
    category = models.CharField(max_length=30,choices=choices,blank=False,default="clover")
    image = models.ImageField(upload_to='product_images/', null=True, blank=True, default='clover.png')
    price = models.DecimalField(max_digits=10, default=0.0, blank=True, decimal_places=2)
    description = models.TextField(default="", blank=False)
    rating = models.IntegerField(default=0, blank=False)
    
    class Meta:
        db_table = 'products'
    
        
    def __str__(self):
        return self.name


    
    
class Order(models.Model):
    user_id = models.CharField(max_length=5, default="None", blank=False)
    products = models.ManyToManyField(Product)  
    order_created = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'orders'
