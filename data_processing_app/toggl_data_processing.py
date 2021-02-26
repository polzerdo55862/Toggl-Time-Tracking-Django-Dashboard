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
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import datetime
import data_processing_app.models as models


def collect_data_from_toggl():
    toggl_api = config.toggl_api_token
    email, workspaces, headers = connect_to_toggl(toggl_api)

    my_workspace = workspaces[0]['id']
    my_workspace_name = workspaces[0]['name']

    #clear table
    #models.toggl_workspaces.objects.all().delete()

    new_workspace = models.toggl_workspaces(wid=my_workspace, name=my_workspace_name)
    new_workspace.save()

    clients, projects = get_all_clients_and_projects(my_workspace, headers)

    start_date = config.start_date
    end_date = config.end_date
    time_entries_extended_df = get_all_time_entries(headers, start_date=start_date,
                                                    end_date=end_date)
    #process the information
    projects_df, clients_df, time_entries_df = data_processing(clients, projects, time_entries_extended_df)

    #fill NaN fields with "-"
    time_entries_df = time_entries_df.fillna("-")

    #ignore entries which has not ended yet
    time_entries_df = time_entries_df[time_entries_df.duration > 0]

    #clear tables
    models.toggl_clients.objects.all().delete()
    models.toggl_projects.objects.all().delete()
    models.time_entries.objects.all().delete()

    #fill tables
    for index, row in clients_df.iterrows():
        new_client = models.toggl_clients(cid=row.cid, workspace=models.toggl_workspaces.objects.get(wid=my_workspace),
                                          name=row.client_name)
        new_client.save()

    for index, row in projects_df.iterrows():
        new_project = models.toggl_projects(pid=row.pid, client=models.toggl_clients.objects.get(cid=row.cid),
                                            project_name=row.project_name)
        new_project.save()

    for index, row in time_entries_df.iterrows():
        new_time_entry = models.time_entries(id=row.id,
                                             project=models.toggl_projects.objects.get(pid=int(row.pid)),
                                             start=row.start,
                                             duration=row.duration)
        new_time_entry.save()

    return projects_df, clients_df, time_entries_df, my_workspace

def web_scraper_puplic_holidays():
    url = 'https://www.ferienwiki.de/feiertage/de/bayern'
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')
    td = soup.findAll('td')

    public_holidays = []

    for line in td:
        try:
            match = re.search(r'\d{2}.\d{2}.\d{4}', str(line))
            date = datetime.datetime.strptime(match.group(), '%d.%m.%Y').date()
            public_holidays.append(date)
        except:
            pass

    public_holidays_df = pd.DataFrame(data=public_holidays)
    public_holidays_df = public_holidays_df.rename(columns={0: "days"})

    #clear table
    models.public_holidays.objects.all().delete()

    for index, row in public_holidays_df.iterrows():
        new_entry = models.public_holidays(days=row.days)
        new_entry.save()



def define_target_working_hours():
    start_date = config.start_date
    end_date = config.end_date
    working_days_df = define_working_days_table(start_date, end_date)

    #clear table
    models.day_types.objects.all().delete()

    for index, row in working_days_df.iterrows():
        new_days_entry = models.day_types(days=row.days,
                                             type=row.type,
                                             working_hours=row.working_hours
                                          )
        new_days_entry.save()

    working_days_df["week"] = [item.strftime("%Y-%V") for item in working_days_df['days']]

    working_days_sum_by_week_df = working_days_df.groupby(['week'])
    working_days_sum_by_week_df = working_days_sum_by_week_df['working_hours'].agg(np.sum)
    working_days_sum_by_week_df = pd.DataFrame(working_days_sum_by_week_df)

#use only once for load data
#web_scraper_puplic_holidays()
# collect_data_from_toggl()
# define_target_working_hours()