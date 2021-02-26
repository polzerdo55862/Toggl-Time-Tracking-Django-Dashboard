from django.http import Http404
from django.shortcuts import render
from data_processing_app.models import toggl_clients
import data_processing_app.models as models
from django.db.models.functions import ExtractWeek, ExtractYear
from django.db.models import Sum
import data_processing_app.toggl_data_processing as data_processing
import plotly.offline as opy
import plotly.graph_objs as go
from django.shortcuts import render
from plotly.offline import plot
from plotly.graph_objs import Scatter
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import datetime
import pandas as pd
import data_processing_app.helper_functions as helper_functions

def visualization(request):
    if request.method == 'POST' and request.POST.get('function') == 'reload_ph':
        data_processing.web_scraper_puplic_holidays()
        data_processing.collect_data_from_toggl()
        data_processing.define_target_working_hours()

    if request.method == 'POST' and request.POST.get('function') == 'reload_toggl_data':
        data_processing.collect_data_from_toggl()
        data_processing.define_target_working_hours()


    context = helper_functions.collect_context()
    # Call the superclass changelist_view to render the page
    return render(request, 'visualization.html', context)

