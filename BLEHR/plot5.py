import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
from collections import deque
import pandas as pd

X = deque(maxlen=100)
X.append(0)
Y = deque(maxlen=100)
Y.append(0)

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        dcc.Graph(id='live-graph', animate=True),
        dcc.Interval(
            id='graph-update',
            interval=1000,
            n_intervals = 0
        ),
    ]
)

@app.callback(Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals')])

def update_graph_scatter(n):
    data_from_csv = pd.read_csv('data.csv')
    X = data_from_csv.iloc[:,0].values.tolist()
    Y = data_from_csv.iloc[:,1].values.tolist()

    data = plotly.graph_objs.Scatter(
            x=list(X),
            y=list(Y),
            name='Scatter',
            mode= 'lines+markers'
            )

    return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
                                                yaxis=dict(range=[min(Y),max(Y)]))}
if __name__ == '__main__':
    app.run_server(debug=True) 