from django.db import models
from api.helpers.models import BaseModel
from django.contrib.postgres.fields import ArrayField
from api.scout.models import Scout
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
    linear_scale_capacity = models.IntegerField(blank=True, null=True)
    

class QualificationAlgorithm(BaseModel):
    name = models.CharField(max_length=255)
    positive_keywords = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    number_positive_keywords = models.IntegerField()
    negative_keywords = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    number_negative_keywords = models.IntegerField()
    score = models.ForeignKey(Score, on_delete=models.CASCADE, null=True, blank=True)


class Scheduler(BaseModel):
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.all_timezones]
    name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=63, choices=TIMEZONE_CHOICES, default='UTC')
    outreach_capacity = models.IntegerField()
    outreach_starttime = models.TimeField()
    outreach_endtime = models.TimeField()
    scrapper_starttime = models.DateTimeField()
    scrapper_endtime = models.DateTimeField(null=True,blank=True)



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
    estimated_usernames = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    photo_links = ArrayField(models.URLField(), blank=True, null=True)
    external_urls = ArrayField(models.URLField(), blank=True, null=True)
    hashtags = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    google_maps_search_keywords = models.TextField(blank=True, null=True)
    enrich_with_url_in_bio = models.BooleanField(default=True)
    is_infinite_loop = models.BooleanField(default=True)



class InstagramUser(BaseModel):
    SOURCE_CHOICES = (
        (1, 'followers'),
        (2, 'searching_users'),
        (3, 'similar_accounts'),
    )
    username = models.CharField(max_length=255,null=True,blank=True)
    info = models.JSONField(null=True,blank=True)
    linked_to = models.CharField(max_length=50,null=True,blank=True)
    source = models.IntegerField(choices=SOURCE_CHOICES,default=1)
    round = models.IntegerField(null=True,blank=True)
    scout = models.ForeignKey(Scout,on_delete=models.CASCADE,null=True,blank=True)
    account_id = models.CharField(max_length=255,null=True,blank=True)
    account_id_pointer = models.BooleanField(default=False)
    outsourced_id = models.CharField(max_length=255,null=True,blank=True)
    outsourced_id_pointer = models.BooleanField(default=False)
    cursor = models.TextField(null=True,blank=True)

    def __str__(self) -> str:

        return self.username if self.username else 'cursor'
