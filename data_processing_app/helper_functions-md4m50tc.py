#import mysql.connector
import base64
from datetime import date, timedelta, timezone
import pandas as pd
import requests
from datetime import datetime
from data_management import settings as config
from urllib.parse import urlencode
import data_processing_app.models as models
from django.db.models.functions import ExtractWeek, ExtractYear
from django.db.models import Sum
import data_processing_app.toggl_data_processing as data_processing
from plotly.offline import plot
from plotly.graph_objs import Scatter
import plotly.graph_objs as go

def connect_to_toggl(api_token):
    """Connect to toggl and get response containing information to the
    :param api_token:   Token for you user profile, you can find the token at
                        Toggl.com at the end of the profile settings page
    """

    string = api_token + ':api_token'
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(string.encode('ascii')).decode("utf-8")}
    url = 'https://www.toggl.com/api/v8/me'

    response = requests.get(url, headers=headers)
    response = response.json()
    email = response['data']['email']
    workspaces = [{'name': item['name'], 'id': item['id']} for item in response['data']['workspaces'] if
                  item['admin'] == True]

    return email, workspaces, headers

def get_all_clients_and_projects(my_workspace, headers):
    '''Gets all clients and projects for your workspace id'''

    url = 'https://www.toggl.com/api/v8/workspaces/' + str(my_workspace) + '/clients'
    clients = requests.get(url, headers=headers).json()

    url = 'https://www.toggl.com/api/v8/workspaces/' + str(my_workspace) + '/projects'
    projects = requests.get(url, headers=headers).json()

    return clients, projects

def get_all_time_entries(headers, start_date, end_date):
    '''Finds all time entries in the time frame [start_date - end_date]'''
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.min.time())

    start_date = start_date.replace(tzinfo=timezone.utc).isoformat()
    end_date = end_date.replace(tzinfo=timezone.utc).isoformat()

    url = 'https://api.track.toggl.com/api/v8/time_entries?'
    params = {'start_date': start_date, 'end_date': end_date}
    url = url + '{}'.format(urlencode(params))

    time_entries = requests.get(url, headers=headers).json()
    return time_entries

def data_processing(clients,projects,time_entries):
    '''Join clients, projects and time entries to a data frame with all time entries
    and the corresponding information to clients and projects'''

    projects_filtered = [{'pid': item['id'],
                          'cid': item['cid'],
                          'project_name': item['name']} for item in projects]

    clients_filtered = [{'cid': item['id'],
                         'client_name': item['name']} for item in clients]

    projects_df = pd.DataFrame(data=projects_filtered)
    clients_df = pd.DataFrame(data=clients_filtered)
    time_entries_df = pd.DataFrame(data=time_entries)

    # join_projects_clients = projects_df.set_index('cid').join(clients_df.set_index('cid'))
    # time_entries_extended_df = time_entries_df.set_index('pid').join(join_projects_clients.set_index('pid'))

    return projects_df, clients_df, time_entries_df

def define_working_days_table(start_date, end_date):
    """
    :return:    Returns a data frame with all days in the defined time frame (start_date - end_date)
                The data frame has two columns: days and type
                :Days: contains all dates in the time frame
                :Type: the information if the day is a
                        - working day (WD)
                        - vacation day (paid time off - PTO)
                        - public holiday (PH)
                        - weekend (WE) - saturday and sunday
    """

    #retrive objects from public_holidays tables an write them in a list
    public_holidays = [item.days for item in models.public_holidays.objects.all()]
    vacation_days = [item.days for item in models.vacation_days.objects.all()]

    all_days = []
    number_of_days = end_date - start_date
    for n in range(number_of_days.days):
        day = start_date + timedelta(n)
        all_days.append({'days': day, 'type': "WD"})

    workdays_index = [0, 1, 2, 3, 4]
    all_days_we = []
    for item in all_days:
        if date.weekday(item['days']) in workdays_index:
            all_days_we.append({'days': item['days'], 'type': item['type']})
        else:
            all_days_we.append({'days': item['days'], 'type': "WE"})

    all_days_we_ph = []
    for item in all_days_we:
        if item['days'] in public_holidays:
            all_days_we_ph.append({'days': item['days'], 'type': "PH"})
        else:
            all_days_we_ph.append({'days': item['days'], 'type': item['type']})

    all_days_we_ph_pto = []
    for item in all_days_we_ph:
        if item['days'] in vacation_days:
            all_days_we_ph_pto.append({'days': item['days'], 'type': "PTO"})
        else:
            all_days_we_ph_pto.append({'days': item['days'], 'type': item['type']})

    print(f"Number of days between start and end date: {len(all_days_we_ph_pto)}")
    print(f"Number of weekend days between start and end date: {len([1 for item in all_days_we_ph_pto if item['type'] == 'WE'])}")
    print(f"Number of public holidays between start and end date (minus public holidays): {len([1 for item in all_days_we_ph_pto if item['type'] == 'PH'])}")
    print(f"Number of vacation days between start and end date (minus public holidays and vacation days): {len([1 for item in all_days_we_ph_pto if item['type'] == 'PTO'])}")

    working_days = []
    for item in all_days_we_ph_pto:
        if item['type'] == "WD":
            working_days.append({'days': item['days'], 'type': item['type'], 'working_hours': config.target_hours_per_day})
        else:
            working_days.append({'days': item['days'], 'type': item['type'], 'working_hours': 0})

    working_days_df = pd.DataFrame(data=working_days)
    return working_days_df

def input_vacation_days():
    pass


def write_toggl_data_in_database(cursor, cnx, time_entries_extended):
    return_messages=[]
    try:
        cursor.execute("CREATE TABLE `dashboard`.`toggl_time_entries` ("
                       "`id` INT NOT NULL,"
                       "`start` DATETIME NULL,"
                       "`stop` DATETIME NULL,"
                       "`duration` INT NULL,"
                       "`description` VARCHAR(45) NULL,"
                       "`project_name` VARCHAR(45) NULL,"
                       "`client_name` VARCHAR(45) NULL,"
                       "PRIMARY KEY (`id`));")
        cnx.commit()
    except mysql.connector.Error as e:
        return_messages.append("Error code:" + str(e.errno))
        return_messages.append("SQLSTATE value:" + str(e.sqlstate))
        return_messages.append("Error message:" + str(e.msg))
        return_messages.append("Error:" + str(e))

        try:
            cursor.execute("DROP TABLE `dashboard`.`toggl_time_entries`")
            return_messages.append("Current table toggl_time_entries was deleted successfully")
        except:
            return_messages.append("Error while deleting table toggl_time_entries")

        try:
            cursor.execute("CREATE TABLE `dashboard`.`toggl_time_entries` ("
                           "`id` INT NOT NULL,"
                           "`start` DATETIME NULL,"
                           "`stop` DATETIME NULL,"
                           "`duration` INT NULL,"
                           "`description` VARCHAR(45) NULL,"
                           "`project_name` VARCHAR(45) NULL,"
                           "`client_name` VARCHAR(45) NULL,"
                           "PRIMARY KEY (`id`));")
            cnx.commit()
            return_messages.append("Table toggl_time_entries was created successfully")
        except:
            return_messages.append("Error while creating table toggl_time_entries")

    # Create a new record
    sql = "INSERT INTO `toggl_time_entries` (`id`, `start`, `stop`, `duration`, `description`, `project_name`, `client_name`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    for index, line in time_entries_extended.iterrows():
        if int(line['duration']) > 0:
            try:
                cursor.execute(sql, (line['id'],
                                     line['start'],
                                     line['stop'],
                                     line['duration'],
                                     line['description'],
                                     line['project_name'],
                                     line['client_name']))
                cnx.commit()
            except mysql.connector.Error as e:
                return(return_messages.append("Fail during ADDING ROWS to table toggl_time_entries"))
                return_messages.append("Error code:" + str(e.errno))
                return_messages.append("SQLSTATE value:" + str(e.sqlstate))
                return_messages.append("Error message:" + str(e.msg))
                return_messages.append("Error:" + str(e))

    return return_messages

def write_working_days_list(cursor, cnx, working_days_df):
    '''Creates the table working_days in the mysql database'''

    return_messages=[]
    try:
        cursor.execute("CREATE TABLE `dashboard`.`working_days` ("
                       "`id` INT NOT NULL,"
                       "`days` DATETIME NULL,"
                       "`type` VARCHAR(45) NULL,"
                       "`working_hours` INT NULL,"
                       "PRIMARY KEY (`id`));")
        cnx.commit()
    except mysql.connector.Error as e:
        return_messages.append("Error code:" + str(e.errno))
        return_messages.append("SQLSTATE value:" + str(e.sqlstate))
        return_messages.append("Error message:" + str(e.msg))
        return_messages.append("Error:" + str(e))

        try:
            cursor.execute("DROP TABLE `dashboard`.`working_days`")
            return_messages.append("Current table working_days was deleted successfully")
        except:
            return_messages.append("Error while deleting table working_days")

        try:
            cursor.execute("CREATE TABLE `dashboard`.`working_days` ("
                           "`id` INT NOT NULL,"
                           "`days` DATETIME NULL,"
                           "`type` VARCHAR(45) NULL,"
                           "`working_hours` INT NULL,"
                           "PRIMARY KEY (`id`));")
            cnx.commit()
            return_messages.append("Table working_days was created successfully")
        except:
            return_messages.append("Error while creating table working_days")

    # Create a new record
    sql = "INSERT INTO `working_days` (`id`, `days`, `type`, `working_hours`) VALUES (%s, %s, %s, %s)"
    for index, line in working_days_df.iterrows():
        try:
            cursor.execute(sql, (index,
                                 line['days'],
                                 line['type'],
                                 line['working_hours']))
            cnx.commit()
        except:
            return(return_messages.append("Fail during ADDING ROWS to table working_days"))
            return_messages.append("Error code:" + str(e.errno))
            return_messages.append("SQLSTATE value:" + str(e.sqlstate))
            return_messages.append("Error message:" + str(e.msg))
            return_messages.append("Error:" + str(e))

    return return_messages

def collect_context():
    fig = go.Figure()

    all_clients = models.toggl_clients.objects.all()

    clients_hours_sum = []
    client_name = []
    for client in all_clients:
        chart_data_actual = (
            models.time_entries.objects.filter(project__client__name=client.name)
                .annotate(week=ExtractWeek('start')).values('week') \
                .annotate(year=ExtractYear('start')).values('year', 'week') \
                .annotate(order_field=ExtractYear('start') + "." + ExtractWeek('start')/53).values('year', 'week', 'order_field') \
                .annotate(y=Sum('duration') / 3600) \
                .order_by('order_field')
        )
        xaxis_actual = []
        yaxis_actual = []

        for line in chart_data_actual:
            xaxis_actual.append(str(line["year"]) + "-" + str(line["week"]))
            yaxis_actual.append(float(line["y"]))


        fig.add_trace(go.Bar(
            x=xaxis_actual,
            y=yaxis_actual,
            name='Actual [h]: '+str(client.name) + " - " + str(round(sum(yaxis_actual), 2)) + " h",
        ))

        clients_hours_sum.append(sum(yaxis_actual))
        client_name.append(client.name)

    chart_data_target = (
        models.day_types.objects.filter()\
            .annotate(week=ExtractWeek('days')).values('week')\
            .annotate(year=ExtractYear('days')).values('year', 'week') \
            .annotate(order_field=ExtractYear('days') + "." + ExtractWeek('days') / 53).values('year', 'week',
                                                                                                 'order_field')\
            .annotate(y=Sum('working_hours'))\
            .order_by('order_field')
    )

    xaxis_target = []
    yaxis_target = []

    for line in chart_data_target:
        x = str(line["year"]) + "-" + str(line["week"])
        if x in xaxis_actual:
            xaxis_target.append(str(line["year"]) + "-" + str(line["week"]))
            yaxis_target.append(float(line["y"]))

    time_entries = models.time_entries.objects.all()


    fig.add_trace(go.Bar(
        x=xaxis_target,
        y=yaxis_target,
        name='Target [h]: ' + " - " + str(round(sum(yaxis_target), 2)) + " h",
        marker_color='lightsalmon'
    ))

    # Here we modify the tickangle of the xaxis, resulting in rotated labels.
    fig.update_layout(barmode='group', xaxis_tickangle=-45)
    fig.update_xaxes(type='category')
    plt_div = plot(fig, output_type='div')

    sum_target = sum(yaxis_target)
    # Attach the chart data to the template context
    context = {'plot_div': plt_div,
               'client_names': client_name,
               'client_hours_sum': clients_hours_sum,
               'sum_target': sum_target,
               'overhours': clients_hours_sum[0] - sum_target
               }
    return context