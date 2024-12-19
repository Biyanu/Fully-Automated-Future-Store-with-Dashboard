from threading import Timer
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import os
import numpy as np
import webbrowser
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

# Get database credentials
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

# Construct SQLAlchemy database URL
db_url = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}'
engine = create_engine(db_url)
query = "SELECT * FROM feature_store;"
df = pd.read_sql(query, engine)

# Data preprocessing
df['salesdate'] = pd.to_datetime(df['salesdate'], errors='coerce')
df = df.dropna(subset=['salesdate'])
df['weekday_name'] = df['salesdate'].dt.day_name()
df['itemssold'] = df['itemssold'].astype(int)
df['discount'] = df['discount'].fillna(0)

# Weekday ordering
weekdays_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Aggregated data for plots
weekday_sales = df.groupby('weekday_name')['itemssold'].sum().reset_index()
weekday_sales['weekday_name'] = pd.Categorical(
    weekday_sales['weekday_name'],
    categories=weekdays_order,
    ordered=True
)
weekday_sales.sort_values('weekday_name', inplace=True)

mean_items_sold_region_weekday = df.groupby(['region', 'weekday_name'])['itemssold'].mean().reset_index()
mean_items_sold_region_weekday['weekday_name'] = pd.Categorical(
    mean_items_sold_region_weekday['weekday_name'],
    categories=weekdays_order,
    ordered=True
)

daily_sales = df.groupby('salesdate')[['itemssold', 'discount']].agg(
    total_items_sold=('itemssold', 'sum'),
    avg_discount=('discount', 'mean')
).reset_index()

# Median of items sold by region and freeship status
median_items_sold_region_freeship = df.groupby(['region', 'freeship'])['itemssold'].median().reset_index()

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout
app.layout = html.Div([
    # Dynamic Metrics Section
    html.Div(id='dynamic-metrics', style={'margin-bottom': '20px', 'backgroundColor': '#f8f9fa'}),

    # Dashboard Title
    html.H1(
        "Feature Store Dashboard",
        style={'textAlign': 'center', 'color': 'blue', 'font-size': '36px'}
    ),

    html.P(
        "Explore the sales trends and key metrics from the feature store.",
        style={'textAlign': 'center', 'color': 'gray', 'font-size': '16px', 'margin-bottom': '20px'}
    ),

    # Dropdown Selector
    html.Div(
        dcc.Dropdown(
            id='plot-selector',
            options=[
                {'label': '📊 Total Items Sold by Weekday', 'value': 'total_items_weekday'},
                {'label': '💲 Average Discount by Weekday', 'value': 'avg_discount_weekday'},
                {'label': '🍰 Sales Distribution by Region', 'value': 'sales_distribution_region'},
                {'label': '📊 Distribution of Items Sold by Weekday', 'value': 'items_sold_distribution'},
                {'label': '📈 Mean Items Sold by Region and Weekday', 'value': 'mean_items_region_weekday'},
                {'label': '📊 Items Sold vs Average Discount Scatter Plot', 'value': 'items_discount_scatter'},
                {'label': '📊 Median Items Sold by Region and Free Shipping', 'value': 'median_items_region_freeship'}
            ],
            value='items_sold_distribution',
            style={
                'backgroundColor': '#f0f0f0',
                'border': '2px solid #007bff',
                'color': '#007bff',
                'width': '60%',
                'margin': '0 auto',
                'padding': '5px'
            }
        ),
        style={'textAlign': 'center', 'margin-bottom': '30px'}
    ),

    # Plot Area
    html.Div(
        dcc.Graph(
            id='sales-plot',
            style={'width': '100%', 'height': '600px'}
        ),
        style={
            'display': 'flex',
            'justify-content': 'center',
            'align-items': 'center',
            'margin': '0 auto',
            'width': '100%'
        }
    )
])

# Callback to update the sales plot based on dropdown selection
@app.callback(
    Output('sales-plot', 'figure'),
    Input('plot-selector', 'value')
)
def update_sales_plot(selected_plot):
    if selected_plot == 'total_items_weekday':
        fig = px.bar(
            weekday_sales,
            x='weekday_name',
            y='itemssold',
            title="Total Items Sold by Weekday",
            labels={'itemssold': 'Items Sold', 'weekday_name': 'Weekday'}
        )
        fig.update_layout(xaxis_title="Weekday", yaxis_title="Items Sold")

    elif selected_plot == 'avg_discount_weekday':
        avg_discount = df.groupby('weekday_name')['discount'].mean().reset_index()
        avg_discount['weekday_name'] = pd.Categorical(
            avg_discount['weekday_name'],
            categories=weekdays_order,
            ordered=True
        )
        avg_discount.sort_values('weekday_name', inplace=True)

        fig = px.line(
            avg_discount,
            x='weekday_name',
            y='discount',
            title="Average Discount by Weekday",
            labels={'discount': 'Average Discount', 'weekday_name': 'Weekday'},
            markers=True
        )

    elif selected_plot == 'sales_distribution_region':
        region_sales = df.groupby('region')['itemssold'].sum().reset_index()
        fig = px.pie(
            region_sales,
            names='region',
            values='itemssold',
            title="Sales Distribution by Region"
        )

    elif selected_plot == 'items_sold_distribution':
        # Ensure weekdays are properly ordered
        df['weekday_name'] = pd.Categorical(
            df['weekday_name'],
            categories=weekdays_order,
            ordered=True
        )
        df.sort_values('weekday_name', inplace=True)  # Sort by the ordered weekdays
        
        fig = px.box(
            df,
            x='weekday_name',
            y='itemssold',
            title="Distribution of Items Sold by Weekday",
            labels={'itemssold': 'Items Sold', 'weekday_name': 'Weekday'},
            color='weekday_name'
        )
        fig.update_layout(
            xaxis_title="Weekday",
            yaxis_title="Items Sold"
        )


    elif selected_plot == 'mean_items_region_weekday':
        mean_items_sold_region_weekday['weekday_name'] = pd.Categorical(
            mean_items_sold_region_weekday['weekday_name'],
            categories=weekdays_order,
            ordered=True
        )
        mean_items_sold_region_weekday.sort_values('weekday_name', inplace=True)

        fig = px.line(
            mean_items_sold_region_weekday,
            x='weekday_name',
            y='itemssold',
            color='region',
            title="Mean Items Sold by Region and Weekday",
            labels={'itemssold': 'Mean Items Sold', 'weekday_name': 'Weekday'},
            markers=True
        )

    elif selected_plot == 'items_discount_scatter':
        fig = px.scatter(
            daily_sales,
            x='avg_discount',
            y='total_items_sold',
            title="Items Sold vs Average Discount",
            labels={'avg_discount': 'Average Discount', 'total_items_sold': 'Items Sold'},
            trendline='ols'
        )

    elif selected_plot == 'median_items_region_freeship':
        fig = px.bar(
            median_items_sold_region_freeship,
            x='region',
            y='itemssold',
            color='freeship',
            barmode='group',
            title="Median Items Sold by Region and Free Shipping",
            labels={'itemssold': 'Median Items Sold', 'region': 'Region', 'freeship': 'Free Shipping'}
        )

    return fig

def open_browser():
    webbrowser.open_new("http://127.0.0.1:8051")

# Run the app with automatic browser launch
if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run_server(debug=True, use_reloader=False, port=8051)
