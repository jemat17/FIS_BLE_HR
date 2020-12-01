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

external_stylesheets =['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
	[
		html.Div([ 
			    dcc.Dropdown(
					id='my-dropdown',
					options=[
						{'label': 'Heart rate', 'value': 'HR'},
						{'label': 'Heart rate variability', 'value': 'HRV'}
					],
					value='HR'
				),
				html.Div(dcc.Slider(id="select-range", updatemode='drag',
									  marks={i * 10: str(i * 10) for i in range(0, 21)},
									  min=0, max=100, value=0), className="row", style={"padding": 5})]), 

		dcc.Graph(id='live-graph', animate=True),
		dcc.Interval(
			id='graph-update',
			interval=1000,
			n_intervals = 0
		),
	]		
)

@app.callback(Output('live-graph', 'figure'),
			[Input('graph-update', 'n_intervals'),
			Input('select-range', 'value'),
			Input('my-dropdown', 'value')])


def update_graph_scatter(n, range1, dropdown):
	data_from_csv = pd.read_csv('data.csv')
	if dropdown == 'HRV':
		if len(data_from_csv) > 2:
			data_from_csv['rr'] = data_from_csv['rr'].str.extract(r'([0-9]+)')
			data_from_csv['rr'] = pd.to_numeric(data_from_csv['rr'])
			data_from_csv.iloc[-1,3] = (data_from_csv.iloc[-1,2] - data_from_csv.iloc[-2,2])
			rolling_mean1 = data_from_csv['HRV'].rolling(window=range1).mean()
			X = data_from_csv.iloc[:,0].values.tolist()
			Y = data_from_csv.iloc[:,3].values.tolist()
	else:
		rolling_mean1 = data_from_csv['HR'].rolling(window=range1).mean()
		X = data_from_csv.iloc[:,0].values.tolist()
		Y = data_from_csv.iloc[:,1].values.tolist()

	trace1 = go.Scatter(x=X, y=Y,
						mode='lines', name='Live HR')
	trace_a = go.Scatter(x=X, y=rolling_mean1, mode='lines', yaxis='y', name=f'HR {range1}')

	# data = plotly.graph_objs.Scatter(
	#         x=list(X),
	#         y=list(Y),
	#         name='Scatter',
	#         mode= 'lines+markers'
	#         )
	layout1 = go.Layout(title = 'Live BPM',
						xaxis=dict(
							title="Time [sec]",
							range=[min(X), max(X)],
							linecolor="#BCCCDC",  # Sets color of X-axis line
							showgrid=True  # Removes X-axis grid lines
						),
						yaxis=dict(
							title="BPM",  
							range=[min(Y), max(Y)],
							linecolor="#BCCCDC",  # Sets color of Y-axis line
							showgrid=True ,  # Removes Y-axis grid lines    
						)
	)
	figure = {'data': [trace1],
				'layout': layout1
				}
	figure['data'].append(trace_a)

	return figure #{'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
	#                                            yaxis=dict(range=[min(Y),max(Y)]))}

if __name__ == '__main__':
	app.run_server(debug=True) 
