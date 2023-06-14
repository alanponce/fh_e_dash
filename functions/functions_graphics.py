import pandas as pd 
import plotly.graph_objects as go
from functions.functions_data import get_rolling, get_global_daily, get_rolling_values

def plot_engagements_users(dataset, label):
  """
  dataset: DataFrame
  label: str

  Plot a figure with the Engagements and Unique Users.
  """
  # Initialize figure
  fig = go.Figure()

  # Add Traces
  data = dataset.copy()

  fig.add_trace(
      go.Scatter(x=list(data.index),
                y=list(data.Engagements),
                name="Engagements",
                line=dict(color="#33CFA5")))

  fig.add_trace(
      go.Scatter(x=list(data.index),
                y=list(data.Unique_users),
                name="Unique users",
                line=dict(color="#ffA500", dash="dash")))


  # Set title
  fig.update_layout(title_text=f"{label}")

  return fig

def plot_metrics(dataset, label):
  """
  dataset: DataFrame
  label: str

  Plot a figure with Engagements metrics (mean, quantile25 and quantile75) 
  for each day.
  """
  # Initialize figure
  fig = go.Figure()

  # Add Traces
  df = dataset.copy()

  fig.add_trace(
      go.Scatter(x=list(df.index),
                y=list(df['Mean']),
                name="Mean",
                line=dict(color="#6AF06A")))
  
  fig.add_trace(
      go.Scatter(x=list(df.index),
                y=list(df.Quantile_75),
                name="Quantile 75",
                line=dict(color="#6a6af0", dash="dash")))
  fig.add_trace(
      go.Scatter(x=list(df.index),
                y=list(df.Quantile_25),
                name="quantile 25",
                line=dict(color="#ffA500", dash="dash")))
  # Set title
  fig.update_layout(title_text= label)
  
  return fig


def get_engagements_by_age(dataset, start, end, label):
  """
  dataset: DataFrame
  label: str

  Plot three figures (Rolling 7, 30 and 90 days) with Quantity of Engagements and Unique Users
  for each day.
  """
  # Filter by bin
  ds_filted_by_age = dataset[dataset['Age'].between(start, end)]
  global_metrics_by_age = get_global_daily(ds_filted_by_age)

  # Rolling
  rolled_7 = get_rolling(global_metrics_by_age, 7, ds_filted_by_age)
  rolled_30 = get_rolling(global_metrics_by_age, 30, ds_filted_by_age)
  rolled_90 = get_rolling(global_metrics_by_age, 90, ds_filted_by_age)

  # Plot
  return plot_engagements_users(rolled_7, f'7 days | {label}'),  plot_engagements_users(rolled_30, f'30 days | {label}'), plot_engagements_users(rolled_90, f'90 days | {label}')
   
def get_metrics_by_age(dataset, start, end, label):
  """
  dataset: DataFrame
  label: str

  Plot three figures (Rolling 7, 30 and 90 days) with Metrics: Mean, Quantile 25 and Quantile 75
  of Engagements and Unique Users rolled.
  """
  # Filter by bin
  ds_filted_by_age = dataset[dataset['Age'].between(start, end)]

  # Rolling
  rolled_metrics_7 = get_rolling_values(ds_filted_by_age, 7)
  rolled_metrics_30 = get_rolling_values(ds_filted_by_age, 30)
  rolled_metrics_90 = get_rolling_values(ds_filted_by_age, 90)

  # Plot
  return plot_metrics(rolled_metrics_7, f'7 days | {label}'), plot_metrics(rolled_metrics_30, f'30 days | {label}'), plot_metrics(rolled_metrics_90, f'90 days | {label}')
