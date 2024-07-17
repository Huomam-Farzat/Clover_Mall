from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    products = models.ManyToManyField(Product)
    date = models.DateTimeField(auto_now_add=True)
