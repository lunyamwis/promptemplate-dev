from django.db import models
from base.models import BaseModel
from product.models import Product
# Create your models here.


class ToneOfVoice(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()

    


class Prompt(BaseModel):
    name = models.CharField(max_length=50)
    data = models.JSONField(default=dict)
    text_data = models.TextField(default='')
    tone_of_voice = models.ForeignKey(ToneOfVoice,on_delete=models.CASCADE, 
                                      null=True, blank=True)
    product = models.ForeignKey(Product,on_delete=models.CASCADE, 
                                      null=True, blank=True)
    
    

    def __str__(self):
        return self.name



class Query(BaseModel):
    name = models.CharField(max_length=255)
    query = models.TextField()
    prompt = models.ForeignKey(Prompt,on_delete=models.CASCADE, 
                                      null=True, blank=True)
    
    def __str__(self) -> str:
        return self.name