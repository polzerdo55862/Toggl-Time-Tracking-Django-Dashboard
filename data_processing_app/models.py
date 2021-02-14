from django.db import models

# Create your models here.
class config(models.Model):
    toggl_api_token = models.CharField(max_length=100)
    start_of_time_frame = models.DateField()
    end_of_time_frame = models.DateField()

class vacation_days(models.Model):
    days = models.DateField()

class public_holidays(models.Model):
    days = models.DateField()

class day_types(models.Model):
    days = models.DateField()
    type = models.CharField(max_length=5)
    working_hours = models.FloatField()

class toggl_workspaces(models.Model):
    wid = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)

class toggl_clients(models.Model):
    cid = models.IntegerField(primary_key=True)
    workspace = models.ForeignKey(toggl_workspaces, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

class toggl_projects(models.Model):
    pid = models.IntegerField(primary_key=True)
    client = models.ForeignKey(toggl_clients, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=100)

class time_entries(models.Model):
    id = models.IntegerField(primary_key=True)
    project = models.ForeignKey(toggl_projects, on_delete=models.CASCADE)
    start = models.DateTimeField()
    duration = models.FloatField()