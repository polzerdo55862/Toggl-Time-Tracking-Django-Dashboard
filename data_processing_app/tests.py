from django.test import TestCase
import os
import django
from sqlalchemy import create_engine

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'data_management.settings')
django.setup()

import data_processing_app.models as models
from data_processing_app.helper_functions import connect_to_toggl, \
    get_all_clients_and_projects, get_all_time_entries, data_processing, \
    define_working_days_table, write_toggl_data_in_database, \
    write_working_days_list
from data_management import settings as config
from django.conf import settings
from datetime import datetime
import pandas as pd
import sys
import matplotlib.pyplot as plt
import numpy as np
import copy
import os
import django

# Create your tests here.
from django.db.models import Sum

duration = models.time_entries.objects.filter(id='1834037702').aggregate(Sum('duration'))


from django.db.models.functions import ExtractWeek
import datetime as dt

last_30 = dt.date.today() - dt.timedelta(days=7)
# order_data = models.time_entries.objects.filter(
#     date__gt=last_30).extra(
#     select={'day': 'date(date)'}.values('day').annotate(
#     total=Sum('total')
# )

from django.db.models.functions import ExtractWeek


week_sum = models.time_entries.objects.filter(project__client__name="DI") \
    .annotate(week=ExtractWeek('start')).values('week') \
    .annotate(week_total=Sum('duration') / 3600) \
    .order_by('week')

for week in week_sum:
    import pdb;pdb.set_trace()