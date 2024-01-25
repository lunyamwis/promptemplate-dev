from django.db import models
from api.helpers.models import BaseModel
from django.contrib.postgres.fields import ArrayField

import pytz

# Create your models here.
class Score(BaseModel):
    CRITERIA = (
        (0, 'none'),
        (1, 'type of keywords and number'),
        (2, 'number of times lead found during scrapping'),
        (3, 'negative points when disqualifying them'),
        (4, 'progress through sales funnel')
    )
    MEASURES = (
        (0, 'percentage'),
        (1, 'probability'),
        (2, 'linear scale')
    )
    name = models.CharField(max_length=255)
    criterion = models.IntegerField(choices=CRITERIA, default=0)
    measure = models.IntegerField(choices=MEASURES, default=0)
    linear_scale_capacity = models.IntegerField()
    

class QualificationAlgorithm(BaseModel):
    name = models.CharField(max_length=255)
    positive_keywords = models.TextField()
    number_positive_keywords = models.IntegerField()
    negative_keywords = models.TextField()
    number_negative_keywords = models.IntegerField()
    score = models.ForeignKey(Score, on_delete=models.CASCADE, null=True, blank=True)


class Scheduler(BaseModel):
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.all_timezones]
    name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=63, choices=TIMEZONE_CHOICES, default='UTC')
    outreach_capacity = models.IntegerField()
    outreach_starttime = models.DateTimeField()
    outreach_endtime = models.DateTimeField()



class LeadSource(BaseModel):
    CRITERIA = (
        (0, 'get similar accounts'),
        (1, 'get followers'),
        (2, 'get posts with hashtag'),
        (3, 'interacted with photos'),
        (4, 'to be enriched from instagram'),
        (5, 'google maps'),
        (6, 'urls')
    )
    name = models.CharField(max_length=255)
    criterion = models.IntegerField(choices=CRITERIA, default=0)
    account_usernames = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    photo_links = ArrayField(models.URLField(), blank=True, null=True)
    hashtags = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    google_maps_search_keywords = models.TextField()
    enrich_with_url_in_bio = models.BooleanField(default=True)
