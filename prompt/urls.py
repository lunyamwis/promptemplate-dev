from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PromptViewSet, RoleViewSet, index, add, update, detail, delete, getPrompt, saveResponse

router = DefaultRouter()
router.register(r"prompts", PromptViewSet, basename="prompts")
router.register(r"roles", RoleViewSet, basename="roles")

urlpatterns = [path("", include(router.urls))]

urlpatterns = [
    path('', index, name='index'),
    path('add/', add, name='add'),
    path('detail/<str:prompt_id>/', detail, name='detail'),
    path('update/<str:prompt_id>/', update, name='update'),
    path('delete/<str:prompt_id>/', delete, name='delete'),
    path('get-prompt/', getPrompt.as_view()),
    path('save-response/',saveResponse.as_view()),
    path("", include(router.urls))
]
