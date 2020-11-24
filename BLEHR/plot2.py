import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

# Program that updates layout automatic

app = dash.Dash()

data = pd.read_csv('data.csv')
time_data = data["time"]
hr_data = data["y"]


app.layout = html.Div(children=[
    dcc.Input(id = 'input', value = 'Enter something', type = 'text'),
    html.Div(id = 'input')
    ])

@app.callback( # @ is called a decorader or a wrapper
    Output(component_id = 'output', component_property = 'children'),
    [Input(component_id = 'input', component_property = 'value')])

def update_value(input_data):
    try:
        return str(float(input_data)**2)
    except:
        return "Some error"

if __name__ == '__main__':
    app.run_server(debug=True)