from django.contrib import admin
from django.urls import path
from data_processing_app import views

urlpatterns = [
    #path('reload_ph/', views.reload_public_holidays, name='reload_ph'),
    path('admin', admin.site.urls),
    path('reload_ph', views.reload_ph),
    path('reload_toggl', views.reload_toggl),
    path('', views.visualization),
]

