from django.db import models
from base.models import BaseModel
# Create your models here.




class Company(BaseModel):
    name = models.CharField(max_length=255)
    database_credentials = models.JSONField()

class Product(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    company = models.ForeignKey(Company,on_delete=models.CASCADE, 
                                      null=True, blank=True)
      
class Problem(BaseModel):
    name = models.CharField(max_length=255)
    product = models.ForeignKey(Product,on_delete=models.CASCADE, 
                                      null=True, blank=True)
    gsheet_formula = models.TextField()


class Solution(BaseModel):
    name = models.CharField(max_length=255)
    gsheet_formula = models.TextField()
    problem = models.ForeignKey(Problem,on_delete=models.CASCADE, 
                                      null=True, blank=True)
    