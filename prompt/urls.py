from django.urls import path
from .views import index, add, update, detail, delete, GetPrompt


urlpatterns = [
    path('', index, name='index'),
    path('add/', add, name='add'),
    path('detail/<str:prompt_id>/', detail, name='detail'),
    path('update/<str:prompt_id>/', update, name='update'),
    path('delete/<str:prompt_id>/', delete, name='delete'),
    path('get-prompt/', GetPrompt.as_view()),
]
