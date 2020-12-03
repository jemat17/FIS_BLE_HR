import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
from collections import deque
import pandas as pd

X = deque(maxlen=100) # Create the x and y deque
X.append(0)
Y = deque(maxlen=100)
Y.append(0)

external_stylesheets =['https://codepen.io/chriddyp/pen/bWLwgP.css'] # Specify the css style sheet

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
	[
		html.Div([ 
			    dcc.Dropdown( # Create the dropdown menu with two elements
					id='my-dropdown',
					options=[
						{'label': 'Heart rate', 'value': 'HR'},
						{'label': 'Heart rate variability', 'value': 'HRV'}
					],
					value='HR'
				),
				html.Div(dcc.Slider(id="select-range", updatemode='drag', # Create the slider
									  marks={i * 10: str(i * 10) for i in range(0, 21)},
									  min=0, max=100, value=0), className="row", style={"padding": 5})]), 

		dcc.Graph(id='live-graph', animate=True), # Crete one graph element
		dcc.Interval( # Set update interval for graph
			id='graph-update',
			interval=1000,
			n_intervals = 0
		),
	]		
)

@app.callback(Output('live-graph', 'figure'), # This specifies what id is liked to what value. 
			[Input('graph-update', 'n_intervals'),
			Input('select-range', 'value'),
			Input('my-dropdown', 'value')])


def update_graph_scatter(n, range1, dropdown): # updates the data list. checks if dropdown is HRV or HR.
	data_from_csv = pd.read_csv('data.csv')
	title = ""
	Yname = ''
	miniY = 0
	maxiY = 100
	typeofplot = 'lines'

	if dropdown == 'HRV':
		rolling_mean1 = data_from_csv['HRV'].rolling(window=range1).mean()
		X = data_from_csv.iloc[:,0].values.tolist()
		Y = data_from_csv.iloc[:,3].values.tolist()
		#title = "Live HRV"
		Yname = '[ms]'
		miniY = 0
		maxiY = 250
		typeofplot = 'markers'



	else:
		rolling_mean1 = data_from_csv['HR'].rolling(window=range1).mean()
		X = data_from_csv.iloc[:,0].values.tolist()
		Y = data_from_csv.iloc[:,1].values.tolist()
		#title = "Live HR"
		Yname = 'BPM'
		miniY = min(Y)
		maxiY = max(Y)
		typeofplot = 'lines'

	layout1 = go.Layout(title = title,
		xaxis=dict(
			title="Time [sec]",
			range=[min(X), max(X)],
			linecolor="#BCCCDC",  # Sets color of X-axis line
			showgrid=True  # Removes X-axis grid lines
		),
		yaxis=dict(
			title= Yname,  
			range=[miniY , maxiY],
			linecolor="#BCCCDC",  # Sets color of Y-axis line
			showgrid=True ,  # Removes Y-axis grid lines    
		),margin={'l':50,'r':0.5,'t':100,'b':1}
	)
	trace1 = go.Scatter(x=X, y=Y, mode= typeofplot, name=title)
	trace_a = go.Scatter(x=X, y=rolling_mean1, mode='lines', yaxis='y', name=f'{Yname} {range1}')

	figure = {'data': [trace1],
				'layout': layout1
				}
	figure['data'].append(trace_a)

	return figure 

if __name__ == '__main__': # Main 
	app.run_server(debug=True) 
