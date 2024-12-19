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
import statsmodels.api as sm 
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

    
    return fig
        

        
# Callback for dynamic metrics
@app.callback(
    Output('dynamic-metrics', 'children'),
    Input('plot-selector', 'value')
)
def update_dynamic_metrics(plot_type):
    if plot_type == 'total_items_weekday':
        total_items_sold = weekday_sales['itemssold'].sum()
        return dbc.Row([
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Total Items Sold", className="card-title"),
                    html.H2(f"{total_items_sold:,}", className="card-text"),
                ]),
                color="success", inverse=True
            ), width=4)
        ])
    elif plot_type == 'avg_discount_weekday':
        avg_discount = df.groupby('weekday_name')['discount'].mean()
        highest_discount_day = avg_discount.idxmax()
        highest_discount_value = avg_discount.max()
        lowest_discount_day = avg_discount.idxmin()
        lowest_discount_value = avg_discount.min()
        return dbc.Row([
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Highest Average Discount", className="card-title"),
                    html.H2(f"{highest_discount_day}", className="card-text"),
                    html.P(f"Discount: {highest_discount_value:.2f}")
                ]),
                color="primary", inverse=True
            ), width=4),
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Lowest Average Discount", className="card-title"),
                    html.H2(f"{lowest_discount_day}", className="card-text"),
                    html.P(f"Discount: {lowest_discount_value:.2f}")
                ]),
                color="danger", inverse=True
            ), width=4)
        ])
    elif plot_type == 'sales_distribution_region':
        # Sales Distribution Metrics
        region_sales = df.groupby('region')['itemssold'].sum()
        total_sales = region_sales.sum()
        region_percentages = (region_sales / total_sales) * 100
        highest_region = region_percentages.idxmax()
        highest_percentage = region_percentages.max()
        lowest_region = region_percentages.idxmin()
        lowest_percentage = region_percentages.min()
        return dbc.Row([
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Region with Highest Sales", className="card-title"),
                    html.H2(f"{highest_region}", className="card-text"),
                    html.P(f"Percentage: {highest_percentage:.1f}%")
                ]),
                color="primary", inverse=True
            ), width=4),
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Region with Lowest Sales", className="card-title"),
                    html.H2(f"{lowest_region}", className="card-text"),
                    html.P(f"Percentage: {lowest_percentage:.1f}%")
                ]),
                color="info", inverse=True
            ), width=4)
        ])
    elif plot_type == 'items_sold_distribution':
        # Variability and Median Metrics
        weekday_medians = df.groupby('weekday_name')['itemssold'].median()
        highest_median_day = weekday_medians.idxmax()
        highest_median_value = weekday_medians.max()
        lowest_median_day = weekday_medians.idxmin()
        lowest_median_value = weekday_medians.min()
        weekday_iqr = df.groupby('weekday_name')['itemssold'].agg(
            lambda x: x.quantile(0.75) - x.quantile(0.25)
        )
        highest_iqr_day = weekday_iqr.idxmax()
        highest_iqr_value = weekday_iqr.max()
        return dbc.Row([
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Highest Median Sales", className="card-title"),
                    html.H2(f"{highest_median_day}", className="card-text"),
                    html.P(f"Median Items Sold: {highest_median_value}")
                ]),
                color="success", inverse=True
            ), width=4),
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Highest Variability (IQR)", className="card-title"),
                    html.H2(f"{highest_iqr_day}", className="card-text"),
                    html.P(f"IQR: {highest_iqr_value:.0f}")
                ]),
                color="warning", inverse=True
            ), width=4)
        ])
    elif plot_type == 'mean_items_region_weekday':
        # Mean Items Sold by Region Metrics
        region_means = mean_items_sold_region_weekday.groupby('region')['itemssold'].mean()
        highest_mean_region = region_means.idxmax()
        highest_mean_value = region_means.max()
        lowest_mean_region = region_means.idxmin()
        lowest_mean_value = region_means.min()
        return dbc.Row([
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Region with Highest Mean Sales", className="card-title"),
                    html.H2(f"{highest_mean_region}", className="card-text"),
                    html.P(f"Mean Items Sold: {highest_mean_value:.1f}")
                ]),
                color="primary", inverse=True
            ), width=4),
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Region with Lowest Mean Sales", className="card-title"),
                    html.H2(f"{lowest_mean_region}", className="card-text"),
                    html.P(f"Mean Items Sold: {lowest_mean_value:.1f}")
                ]),
                color="info", inverse=True
            ), width=4)
        ])
    elif plot_type == 'median_items_region_weekday':
        # Median Items Sold by Region Metrics
        region_medians = median_items_sold_region_weekday.groupby('region')['itemssold'].median()
        highest_median_region = region_medians.idxmax()
        highest_median_value = region_medians.max()
        lowest_median_region = region_medians.idxmin()
        lowest_median_value = region_medians.min()
        return dbc.Row([
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Region with Highest Median Sales", className="card-title"),
                    html.H2(f"{highest_median_region}", className="card-text"),
                    html.P(f"Median Items Sold: {highest_median_value:.1f}")
                ]),
                color="primary", inverse=True
            ), width=4),
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Region with Lowest Median Sales", className="card-title"),
                    html.H2(f"{lowest_median_region}", className="card-text"),
                    html.P(f"Median Items Sold: {lowest_median_value:.1f}")
                ]),
                color="info", inverse=True
            ), width=4)
        ])
    elif plot_type == 'items_discount_scatter':
        # Regression and Correlation Metrics
        regression_model = sm.OLS(daily_sales['total_items_sold'], sm.add_constant(daily_sales['avg_discount'])).fit()
        slope = regression_model.params['avg_discount']
        r_squared = regression_model.rsquared
        correlation = np.sqrt(r_squared)  # Correlation is the square root of R-squared
        
        return dbc.Row([
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Regression Slope", className="card-title"),
                    html.H2(f"{slope:.4f}", className="card-text"),
                    html.P("Indicates the impact of discounts on sales.")
                ]),
                color="primary", inverse=True
            ), width=4),
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("Correlation Coefficient (R)", className="card-title"),
                    html.H2(f"{correlation:.2f}", className="card-text"),
                    html.P("Measures the strength of the relationship.")
                ]),
                color="info", inverse=True
            ), width=4)
        ])
    
    return dbc.Row()

def open_browser():
    webbrowser.open_new("http://127.0.0.1:8051")

# Run the app with automatic browser launch
if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run_server(debug=True, use_reloader=False, port=8051)
