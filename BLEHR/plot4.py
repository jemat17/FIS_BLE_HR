import dash
import dash_core_components as dcc
import dash_html_components as html
import time
from collections import deque
import plotly.graph_objs as go
import pandas as pd

app = dash.Dash('HR_data')

data_dict = {"time":time_data,
"HR": hr_data}

def updata_obd_values(time_data, hr_data):
    data = pd.read_csv('data.csv')
    time_data.append(data['time'])
    hr_data.append(data['y'])

    return time_data, hr_data
        
    
app.layout = html.Div([
    html.Div([
        html.H2('HR Data',
                style={'float': 'left',
                       }),
        ]),
    dcc.Dropdown(id='data', #Id is input for data.
                 options=[{'label': 'HR live', 'value': hr_data} #Dropdown menu for choosing a graph
                 value='hr_data',
                 multi=True
                 ),
    html.Div(children=html.Div(id='graphs'), className='row'),
    dcc.Interval( #Live updata
        id='graph-update',
        interval=100),
    ], className="container",style={'width':'98%','margin-left':10,'margin-right':10})

@app.callback(
    dash.dependencies.Output('graphs','children'),
    [dash.dependencies.Input('data', 'value')],
    events=[dash.dependencies.Event('graph-update', 'interval')]
    )


def update_graph(data_names):
    global time_data
    global hr_data
    time_data, hr_data = update_obd_values(time_data, hr_data)


    if len(data_names)>2:
        class_choice = 'col s12 m6 l4' #size of screen
    elif len(data_names) == 2:
        class_choice = 'col s12 m6 l6'
    else:
        class_choice = 'col s12'


    

    data = go.Scatter(
        x=list(time_data),
        y=list(data_dict['hr_data]),
        name='Scatter',
        fill="tozeroy",
        fillcolor="#6897bb"
        )

    graphs.append(html.Div(dcc.Graph(
        id=data_name,
        animate=True,
        figure={'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(time_data),max(time_data)]),
                                                    yaxis=dict(range=[min(data_dict['hr_data']),max(data_dict['hr_data'])]),
                                                    margin={'l':50,'r':1,'t':45,'b':1},
                                                    title='{}'.format('hr_data'))}
        ), className=class_choice))

    return graphs

external_css = ["https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css"]
for css in external_css:
    app.css.append_css({"external_url": css})

external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js']
for js in external_css:
    app.scripts.append_script({'external_url': js})

if __name__ == '__main__':
    app.run_server(debug=True)
