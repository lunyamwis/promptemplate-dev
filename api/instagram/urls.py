from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'scores', views.ScoreViewSet)
router.register(r'qualification_algorithms', views.QualificationAlgorithmViewSet)
router.register(r'schedulers', views.SchedulerViewSet)
router.register(r'lead_sources', views.LeadSourceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('scrapFollowersOrSimilarAccounts/', views.GetFollowersOrSimilarAccounts.as_view()),
    path('scrapFollowersToCSV/', views.GetFollowersToCSV.as_view()),
    path('setup/', views.SetupScrapper.as_view()),
]

