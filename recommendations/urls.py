
from django.urls import path
from .views import frequent_patterns_view

urlpatterns = [
    path('frequent-patterns/', frequent_patterns_view, name='frequent_patterns'),
]