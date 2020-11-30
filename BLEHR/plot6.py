import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output


df_aapl_raw = pd.read_csv("data/AAPL.csv")
df_hr_raw = pd.read_csv("data.csv")


df_aapl_slice['Year'] = pd.DatetimeIndex(df_aapl_slice['Date']).year
df_hr_time['Time'] = pd.DatetimeIndex(df_hr_raw['Time']).day

external_stylesheets =['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div([html.H1("Moving Average Crossover Strategy For Apple Stocks ")], style={'textAlign': "center"}),
    html.Div([
        html.Div([
            html.Div([dcc.Graph(id="my-graph")], className="row", style={"margin": "auto"}),
            html.Div([html.Div(dcc.RangeSlider(id="Day selection", updatemode='drag',
                                               marks={i: '{}'.format(i) for i in df_hr_time.Day.unique().tolist()},
                                               min=df_hr_time.Day.min(), max=df_hr_time.Day.max(), value=[2014, 2019]),
                               className="row", style={"padding-bottom": 30,"width":"60%","margin":"auto"}),
                      html.Span("Moving Average : Select Window Interval", className="row",
                                style={"padding-top": 30,"padding-left": 40,"display":"block",
                                       "align-self":"center","width":"80%","margin":"auto"}),
                      html.Div(dcc.Slider(id="select-range1", updatemode='drag',
                                          marks={i * 10: str(i * 10) for i in range(0, 21)},
                                          min=0, max=200, value=50), className="row", style={"padding": 10}),
                      html.Div(dcc.Slider(id="select-range2", updatemode='drag',
                                          marks={i * 10: str(i * 10) for i in range(0, 21)},
                                          min=0, max=200, value=170), className="row", style={"padding": 10})

                      ], className="row")
        ], className="six columns",style={"margin-right":0,"padding":0}),
        html.Div([
            dcc.Graph(id="plot-graph")
        ], className="six columns",style={"margin-left":0,"padding":0}),
    ], className="row")
   ], className="container")


@app.callback(
    Output("my-graph", 'figure'),
    [Input("day selection", 'value'),
     Input("select-range1", 'value'),
     Input("select-range2", 'value')])
def update_ma(day, range1, range2):
    df_apl = df_hr_time[(df_hr_time["Time"] >= day[0]) & (df_hr_time["Time"] <= day[1])]

    rolling_mean1 = df_apl['HR'].rolling(window=range1).mean()

    trace1 = go.Scatter(x=df_apl['Time'], y=df_apl['HR'],
                        mode='lines', name='Heart rate')
    trace_a = go.Scatter(x=df_apl['Time'], y=rolling_mean1, mode='lines', yaxis='y', name=f'SMA {range1}')
    
    layout1 = go.Layout({'title': 'Stock Price With Moving Average',
                         "legend": {"orientation": "h","xanchor":"left"},
                         "xaxis": {
                             "rangeselector": {
                                 "buttons": [
                                     {"count": 6, "label": "6M", "step": "month",
                                      "stepmode": "backward"},
                                     {"count": 1, "label": "1Y", "step": "year",
                                      "stepmode": "backward"},
                                     {"count": 1, "label": "YTD", "step": "year",
                                      "stepmode": "todate"},
                                     {"label": "5Y", "step": "all",
                                      "stepmode": "backward"}
                                 ]
                             }}})

    figure = {'data': [trace1],
              'layout': layout1
              }
    figure['data'].append(trace_a)
    return figure


@app.callback(
    Output("plot-graph", 'figure'),
    [Input("year selection", 'value')])
def update_return(year):

    df_apl = df_hr_time[(df_hr_time["Time"] >= day[0]) & (df_hr_time["Time"] <= day[1])]

    stocks = pd.DataFrame({"HR": df_apl["HR"]})
    stocks = stocks.set_index('Time')
    stock_return = stocks.apply(lambda x: ((x - x[0]) / x[0])*100)

    trace2 = go.Scatter(x=df_sp['Time'], y=stock_return['HR'], mode='lines', name='Heart rate')

    layout2 = go.Layout({'title': 'Returns (%) : AAPL vs S&P 500 ',
                         "legend": {"orientation": "h","xanchor":"left"}, })

    fig = {'data': [trace2],
           'layout': layout2
           }
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)