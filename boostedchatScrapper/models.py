from django.db import models
from api.helpers.models import BaseModel

class Link(BaseModel):
    url = models.URLField()
    pointer = models.BooleanField(default=False)
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name
    


class ScrappedData(models.Model):
    name = models.CharField(max_length=255)
    response = models.JSONField()

    def __str__(self) -> str:
        return self.name