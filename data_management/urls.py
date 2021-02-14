from django.contrib import admin
from django.urls import path
from data_processing_app import views

urlpatterns = [
    path('admin', admin.site.urls),
    path('', views.visualization),
]

