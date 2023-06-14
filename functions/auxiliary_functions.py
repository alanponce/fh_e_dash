import pandas as pd
import datetime as dt
import plotly.graph_objects as go
import plotly.express as px

from dateutil.relativedelta import relativedelta

# Read_all_csv files
def read_csvs(funding_route, churned_route, subsequent_route):
  """
  funding_route: str
  churned_route: str
  subsequent_route: str
  
  return: three dataframes funding, churned, subsequent in that order
  """

  funding = pd.read_csv(funding_route)
  subsequent = pd.read_csv(subsequent_route)
  churned = pd.read_csv(churned_route)
  return funding, churned, subsequent

def filter_by_date(df, from_date, days=0):
  """
  df: dataframe
  from_date: From date where the loockback will be calculated format: 'YYYY-MM-DD'
  days: int, default 0
  
  return: filtered dataframe
  """
  if days == 0:
    filtered_ds = df.loc[from_date]
  else:
    min_date = pd.to_datetime(from_date, utc=True)
    max_date = pd.to_datetime(from_date, utc=True) + dt.timedelta(days=days)

    # Define two masks
    mask1 = df.index >= min_date
    mask2 = df.index <= max_date

    # Apply the masks to the DataFrame
    filtered_ds = df[mask1 & mask2]
  return filtered_ds

def convert_dates(df, index = True):
  """
  df: dataframe
  index: bool

  return: df with change type in datatime 
  """
  df['EventDateTime'] = pd.to_datetime(df['EventDateTime'])
  df['EventDateTime'] = pd.to_datetime(df['EventDateTime'].dt.normalize())

  if index:
    df.set_index('EventDateTime', inplace = True)
  return df


def filter_by_month(df, year, month):
    """
    df: dataframe

    return: filtered df
    """  
    date = f'{year}-{month}'
    filtered_ds = df[date]

    return filtered_ds


def get_churned_by_day(funding_ds, churned_ds, subsequent_ds, days):
  """
  funding_ds: dataframe
  churned_ds: dataframe
  subsequent_ds: dataframe
  days: int

  return: dataframe
  """   
  # Creo el nuevo dataset
  new_ds = funding_ds.copy()
  new_ds.reset_index(inplace = True)
  new_ds = new_ds.groupby('EventDateTime')[['AccountNumber']].count()

  # Create other columns
  for day in range(days):
    new_ds[f'{day + 1} Days'] = 0


  for index, date in enumerate(new_ds.index):
    # Le asigno los días que quiero ver
    for column in range(days):
      
      try:
        funding_filtered = filter_by_date(funding_ds, date)
        churned_filtered = filter_by_date(churned_ds, date, column)
        subsequent_filtered = filter_by_date(subsequent_ds, date, column)

        
        funding_accounts = funding_filtered['AccountNumber'].tolist()
        churned_accounts = churned_filtered['AccountNumber'].tolist()
        subsequent_accounts = subsequent_filtered['AccountNumber'].tolist()

        is_churned = churned_filtered['AccountNumber'].isin(funding_accounts)
        is_subsequent = subsequent_filtered['AccountNumber'].isin(funding_accounts)
        
        final_churned = is_churned.sum() - is_subsequent.sum()
        value = new_ds.loc[date, 'AccountNumber'] - final_churned
        division = value / new_ds.loc[date, 'AccountNumber']
        

        new_ds.at[date, f'{column + 1} Days'] = value

      except:
        value = new_ds.loc[date, 'AccountNumber']
        new_ds.at[date, f'{column+1} Days'] = value

  new_ds = new_ds.drop('AccountNumber', axis=1)
  new_ds = new_ds.drop(index=new_ds.index[:2])
  
  # for column in new_ds.columns:
  #   new_ds[column] = new_ds[column].apply(lambda x: '{:.2%}'.format(x))
  
  return new_ds


def get_churned_by_month(funding_ds, churned_ds, subsequent_ds, months):
  """
  funding_ds: dataframe
  churned_ds: dataframe
  subsequent_ds: dataframe
  months: int

  return: dataframe
  """   
  # Creo el nuevo dataset
  new_ds = funding_ds.copy()
  new_ds.reset_index(inplace = True)
  new_ds = new_ds.groupby('EventDateTime')[['AccountNumber']].count()

  # Create other columns
  for day in range(months):
    new_ds[f'{day + 1} Month'] = 0


  for index, date in enumerate(new_ds.index):
    # if date.year == 2023:
    #   break
    # Le asigno los días que quiero ver
    for column in range(months):
      
      try:
        end_date = date + relativedelta(months=column)

        funding_filtered = filter_by_date(funding_ds, date)
        churned_filtered = churned_ds.loc[f"{date.year}-{date.month:02d}":f"{end_date.year}-{end_date.month:02d}"]
        subsequent_filtered = subsequent_ds.loc[f"{date.year}-{date.month:02d}":f"{end_date.year}-{end_date.month:02d}"]

        
        funding_accounts = funding_filtered['AccountNumber'].tolist()
        churned_accounts = churned_filtered['AccountNumber'].tolist()
        subsequent_accounts = subsequent_filtered['AccountNumber'].tolist()

        is_churned = churned_filtered['AccountNumber'].isin(funding_accounts)
        is_subsequent = subsequent_filtered['AccountNumber'].isin(funding_accounts)
        
        final_churned = is_churned.sum() - is_subsequent.sum()
        value = new_ds.loc[date, 'AccountNumber'] - final_churned
        
        new_ds.at[date, f'{column + 1} Month'] = value

      except:    
        value = new_ds.loc[date, 'AccountNumber']
        new_ds.at[date, f'{column+1} Month'] = -1
        print(date, months)

  #new_ds = new_ds.drop('AccountNumber', axis=1)
  new_ds = new_ds.drop(index=new_ds.index[:2])
  
  return new_ds

def get_by_period(dataset, period, percentage = True):
  """starting on Sundays
  For example: Takes 2019-06-09 and sum all days from 06/02 to 06/09
  """
  ds = dataset.copy()
  if period == 'W':
    reemsample = ds.resample('W').sum()
  elif period == 'M':
    reemsample = ds.resample('M').sum()
  elif period == 'Y':
    reemsample = ds.resample('Y').sum()
  elif period == 'MS':
    reemsample = ds.resample('MS').sum()
   
  else:
    reemsample = ds

  if percentage:

    reemsample = reemsample.div(reemsample.iloc[:, 0], axis=0)
    reemsample = reemsample.mul(100)
    for col in reemsample.columns:
      reemsample[col] = reemsample[col].apply(lambda x: '{:.2f}%'.format(x))
  return reemsample

#graph functions 

def plot_values(data_to_plot):
  data_plot = data_to_plot.copy()

  data_plot = data_plot.replace('%', '', regex=True).astype('float') / 100
  data = {}

  for column in data_plot.columns:
    data[column] = data_plot[column].mean()


  df = pd.DataFrame.from_dict(data, orient='index', columns=['Value'])
  df.reset_index(inplace=True)
  df.rename(columns={'index': 'Months'}, inplace=True)

  fig = px.bar(df, x='Months', y='Value', title='Values by Month')
  fig.show()

  x_values = list(data.keys())
  y_values = list(data.values())
  fig = go.Figure()
  fig.add_trace(go.Scatter(x=x_values, y=y_values, mode='lines+markers'))

  fig.update_layout(title='Customer retention rate',
                    xaxis_title='Months since funding',
                    yaxis_title='Percent of Customers',
                    )

  return fig.show()


def graph_values(data, percentage):
  if percentage == True:
    for column in data.columns:
      data[column] = data[column].apply(lambda x: float(x[:5])) 

  data = data.rename(columns={'AccountNumber':'0 Month'})
  
  fig = go.Figure()
  x_values = data.columns
  for i in range(len(data)):
    fila = data.iloc[i]
    fig.add_trace(go.Scatter(x=x_values, y=fila.values, mode='lines+markers', name= f'Cohort {(fila.name).strftime("%Y-%m-%d")}'))

  # Update the layout of the plot
  fig.update_layout(title= f'Porcentaje de retención: {data.shape[1] -1} periodos',
                  xaxis_title='Periodos',
                  yaxis_title='Porcentaje de Retención')

  # Show the plot
  return fig.show()