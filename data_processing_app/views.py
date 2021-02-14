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

def visualization(request):
    if request.method == 'POST':
        data_processing.collect_data_from_toggl()

    # Aggregate new subscribers per day
    chart_data_actual = (
        models.time_entries.objects.filter(project__client__name="DI")
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

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=xaxis_actual,
        y=yaxis_actual,
        name='Actual Hours',
        marker_color='indianred'
    ))
    fig.add_trace(go.Bar(
        x=xaxis_target,
        y=yaxis_target,
        name='Target Hours',
        marker_color='lightsalmon'
    ))

    # Here we modify the tickangle of the xaxis, resulting in rotated labels.
    fig.update_layout(barmode='group', xaxis_tickangle=-45)
    fig.update_xaxes(type='category')
    plt_div = plot(fig, output_type='div')

    # plot_div = plot([Scatter(x=xaxis_target, y=yaxis_target,
    #                     mode='lines', name='test',
    #                     opacity=0.8, marker_color='green')],
    #            output_type='div')

    # Attach the chart data to the template context
    context = {'plot_div': plt_div}

    # Call the superclass changelist_view to render the page
    return render(request, 'visualization.html', context)