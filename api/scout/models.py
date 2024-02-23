from django.db import models
from api.helpers.models import BaseModel

# Create your models here.
class ScoutingMaster(BaseModel):
    name = models.CharField(max_length=255)
    def __str__(self) -> str:
        return super().__str__(self.name)

class Scout(BaseModel):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    available = models.BooleanField(default=False)
    master = models.ForeignKey(ScoutingMaster,on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self) -> str:
        return super().__str__(self.username)