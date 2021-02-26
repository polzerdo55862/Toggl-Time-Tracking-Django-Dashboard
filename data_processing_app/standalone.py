import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'data_management.settings')
django.setup()

import pytz
import data_processing_app.models as models
import pandas as pd
import datetime
import data_processing_app.models as models
from django.db.models.functions import ExtractWeek, ExtractYear
from django.db.models import Sum
import data_processing_app.toggl_data_processing as data_processing
import plotly.offline as opy
import plotly.graph_objs as go
from django.shortcuts import render
from plotly.offline import plot

#Sample data
# workspaces_df = pd.DataFrame({'wid': [4546930], 'name': ["Dans Workspace"]})
#
# clients_df = pd.DataFrame({'cid': [49914568],
#                            'wid': [4546930],
#                            'client_name': ["Dans Computer Service"]})
#
# projects_df = pd.DataFrame({'pid': [163856075, 162758906],
#                             'cid': [49914568, 49914568],
#                             'project_name': ["Project 1", "Project 2"]})
#
# time_entries_df = pd.DataFrame({'id': [1658745021, 1658750905],
#                                 'pid': [163856075, 162758906],
#                                 'start': [datetime.datetime(2013, 11, 20, 20, 8, 7, 127325, tzinfo=pytz.UTC)
#                                     ,datetime.datetime(2013, 11, 21, 20, 8, 7, 127325, tzinfo=pytz.UTC)],
#                                 'duration': [309, 543]})



# for index, row in workspaces_df.iterrows():
#     new_workspace = models.toggl_workspaces(wid=row.wid,
#                                             name=row.name)
#     new_workspace.save()
#
#
# for index, row in clients_df.iterrows():
#     new_client = models.toggl_clients(cid=row.cid,
#                                       workspace=models.toggl_workspaces.objects.get(wid=row.wid),
#                                       name=row.client_name)
#     new_client.save()
#
# for index, row in projects_df.iterrows():
#     new_project = models.toggl_projects(pid=row.pid,
#                                         client=models.toggl_clients.objects.get(cid=row.cid),
#                                         project_name=row.project_name)
#     new_project.save()
#
# for index, row in time_entries_df.iterrows():
#     new_time_entry = models.time_entries(id=row.id,
#                                          project=models.toggl_projects.objects.get(pid=int(row.pid)),
#                                          start=row.start,
#                                          duration=row.duration)
#     new_time_entry.save()

chart_data_target = (
    models.day_types.objects.filter() \
        .annotate(week=ExtractWeek('days')).values('week') \
        .annotate(year=ExtractYear('days')).values('year', 'week') \
        .annotate(order_field=ExtractYear('days') + "." + ExtractWeek('days') / 53).values('year', 'week',
                                                                                           'order_field') \
        .annotate(y=Sum('working_hours')) \
        .order_by('order_field')
)

test = "test"