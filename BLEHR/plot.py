import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

app = dash.Dash()

data = pd.read_csv('data.csv')
time_data = data["time"]
hr_data = data["y"]


app.layout = html.Div(children=[
    html.H1('HR Plotter'),
    dcc.Graph(id = 'example',
              figure = {
                    'data': [{'x':time_data, 
                            'y':hr_data, 
                            'type':'line', 
                            'name':'HR'}
                            ],
                    'layout': {
                        'title':'Basic plotting example'
                    } 
                })
    ])

if __name__ == '__main__':
    app.run_server(debug=True)