from django.urls import path
from . import views

urlpatterns = [
    path('scrapNewUsers/', views.InstagramScrapper.as_view()),
    path('scrapMoxie/', views.InstagramMoxieCsv.as_view()),
]

