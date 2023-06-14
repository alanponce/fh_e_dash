import pandas as pd 
import datetime as dt

def get_engagement_list(df, lookback = 1365, from_date = pd.Timestamp.today()):
  """
  df: DataFrame
  Index: loockback
  from_date: From date where the loockback will be calculated format: 'YYYY-MM-DD'

  return dataframe: engagement lists filtered between the date specified and the loockback.
  """

  ds = df.copy()
  #Change data type
  ds['EventDateTime'] = pd.to_datetime(ds['EventDateTime'])

  # Set min and max date, moving one day in each to take care about time in utf format.
  min_date = pd.to_datetime(from_date, utc=True) - dt.timedelta(days=(lookback - 1)) 
  max_date = pd.to_datetime(from_date, utc=True) + dt.timedelta(days=1)

  # Define two masks
  mask1 = ds['EventDateTime'] > min_date
  mask2 = ds['EventDateTime'] <= max_date

  # Apply the masks to the DataFrame
  engagement_list = ds[mask1 & mask2]
  engagement_list = engagement_list.reset_index(drop=True)
  #engagement_list['EventDateTime'] = pd.to_datetime(engagement_list["EventDateTime"].dt.strftime('%Y-%m-%d'))

  #Convert times to midnight
  engagement_list['EventDateTime'] = pd.to_datetime(engagement_list['EventDateTime'].dt.normalize())
  return engagement_list

def get_global_daily(engagement_list, UserId = []):
  """
  engagement_list: DataFrame
  UserId: List of int

  return dataframe: Grouped number of engagement per day in the last X days.
  """
  ds = engagement_list.copy()
  #if a list is passed, filter the dataframe
  if len(UserId) > 0:
    ds = ds[ds['UserId'].isin(UserId)]

  #Group by  "EventDateTime", count EventDateTime and uniques of UserId
  #The final columns are rename, UserId as Unique_users and EventDateTime as Engagements
  list_with_metrics = ds.groupby('EventDateTime').agg(
      {
      'EventDateTime':'count',
      'UserId':'nunique',
       }
       ).rename(
           columns={'UserId': 'Unique_users',
                    'EventDateTime': 'Engagements'
                    }
                )
  #Get count of EventDateTime between unique users
  list_with_metrics['Engage/UniqueUser'] = list_with_metrics['Engagements'] / list_with_metrics['Unique_users']
 
  return list_with_metrics


def get_rolling(dataset, rolling_quantity, engagement_list):
  """
  dataset: DataFrame
  rolling_quantity: int
  engagement_list: Dataframe 

  return dataframe: Sum of Engagements and unique users in a period of time 
  """  
  #Take only Engagements columns, with EventDateTime as index
  df = dataset[['Engagements']]
  #Provide rolling window calculations, 
  #Size of the moving window is rolling_quantity, and sum the values 
  rolled = df.rolling(rolling_quantity).sum()
  #Create a columns with 1's as value 
  rolled['Unique_users'] = 1
  engagement_list_dataset = engagement_list.copy()
  #Set EventDateTime as index 
  engagement_list_dataset.set_index('EventDateTime', inplace = True)

  #For date in the index, index is EventDateTime
  for date in rolled.index:
    
    # Filter dates
    end_date = pd.to_datetime(date)
    start_date =pd.to_datetime(date - pd.Timedelta(days=rolling_quantity - 1))
    
    #Get unique users in a period of time, from start_date to end_date
    unique_users = engagement_list_dataset.loc[start_date:end_date]['UserId'].nunique()
    #Set the value in the index with the end_date and column Unique_users
    rolled.at[end_date,'Unique_users'] = unique_users
    
  return rolled


def get_daily_users_list(rolled_dataset, engagement_list, lookback):
  """
  rolled_dataset: DataFrame
  engagement_list: DataFrame
  lookback: int

  return dataframe: With the days as index and for each one a list of users that have at least
  1 engagement in the range (day - lookback : day).
  """
  #Select two columns, UserId and EventDateTime
  all_engagements = engagement_list[['UserId','EventDateTime']]
  #Set EventDateTime as index
  all_engagements = all_engagements.set_index('EventDateTime')
  #Create a dataframe with the index of rolled_dataset
  daily_rolled_users_list = pd.DataFrame(index=rolled_dataset.index)
  #Create a columns with "" as value 
  daily_rolled_users_list['Users'] = ''
  for date in rolled_dataset.index:

    end_date = date
    start_date = date - pd.Timedelta(days=lookback-1)
    #User ids in a period of time, in a list  
    user_ids = list(all_engagements.loc[start_date:end_date]['UserId'].values)
    #list of users ids is setted in end_date and Users
    daily_rolled_users_list.at[end_date,'Users'] = user_ids
  
  return daily_rolled_users_list

def get_rolling_values(engagement_list, lookback):
  """
  engagement_list: DataFrame
  lookback: int

  return dataframe: With the days as index and the amount of engagements and unique users in the
  range=(day - lookback : day). The dataset also has the mean, quantile25 and quantile 75 per day.
  """
  #Select two columns
  prueba1 = engagement_list[['UserId','EventDateTime']]
  #Group by UserId and EventDateTime, the result of size is set as Interacciones
  df_grouped = prueba1.groupby(['UserId', 'EventDateTime']).size().reset_index(name='Interacciones')
  #Return reshaped DataFrame organized by given index / column values.
  df_pivoted = df_grouped.pivot(index='EventDateTime', columns='UserId', values='Interacciones')
  #Fill na and sum values in a rolling window calculations
  #window is lookback
  df_rolling = df_pivoted.fillna(0).rolling(window=lookback).sum()
  #Calculations
  df_rolling['Mean'] = df_rolling[df_rolling !=0].mean(axis=1)
  df_rolling['Quantile_25'] = df_rolling[df_rolling !=0].quantile(q=0.25, axis=1, interpolation='nearest')
  df_rolling['Quantile_75'] = df_rolling[df_rolling !=0].quantile(q=0.75, axis=1, interpolation='nearest')

  return df_rolling



def get_engagement_list_v2(df, start_date , end_data):
  """
  df: DataFrame
  start_date: date in 'YYYY-MM-DD'
  end_data : date in 'YYYY-MM-DD'
  return dataframe: engagement lists filtered between two dates
  """
  ds = df.copy()
  #Change data type
  ds['EventDateTime'] = pd.to_datetime(ds['EventDateTime'])

  #Filter the df
  engagement_list = ds[ds["EventDateTime"].between(start_date, end_data )]
  engagement_list = engagement_list.reset_index(drop=True)

  #Convert times to midnight
  engagement_list['EventDateTime'] = pd.to_datetime(engagement_list['EventDateTime'].dt.normalize())
  return engagement_list


def get_rolling_values_version2(engagement_list, lookback):
  """
  engagement_list: DataFrame
  lookback: int

  return dataframe: With the days as index and the amount of engagements and unique users in the
  range=(day - lookback : day). The dataset also has the mean, quantile25 and quantile 75 per day.
  """
  #Select two columns
  prueba1 = engagement_list[['UserId','EventDateTime']]
  #Group by UserId and EventDateTime, the result of size is set as Interacciones
  df_grouped = prueba1.groupby(['UserId', 'EventDateTime']).size().reset_index(name='Interacciones')
  #Return reshaped DataFrame organized by given index / column values.
  df_pivoted = df_grouped.pivot(index='EventDateTime', columns='UserId', values='Interacciones')
  #Fill na and sum values in a rolling window calculations
  #window is lookback
  df_rolling = df_pivoted.fillna(0).rolling(window=lookback).sum()
  #Calculations
  df_rolling['Mean'] = df_rolling[df_rolling !=0].mean(axis=1)
  df_rolling['Quantile_25'] = df_rolling[df_rolling !=0].quantile(q=0.25, axis=1, interpolation='nearest')
  df_rolling['Quantile_75'] = df_rolling[df_rolling !=0].quantile(q=0.75, axis=1, interpolation='nearest')
  
  #pivot to normal dataframe (without multi index in columns )
  df_rolling = pd.DataFrame(df_rolling.to_records())
  #columns with UserId
  columnas_userId = df_rolling.columns[1: -3]
  #userId to rows 
  df_rolling = pd.melt(df_rolling, id_vars=['EventDateTime','Mean', 'Quantile_25', 'Quantile_75'], 
                       value_vars=columnas_userId, 
                       var_name ='UserId', value_name ='Num_interacciones')
  return df_rolling

def get_rolling_values_version3(engagement_list, lookback):
  """
  engagement_list: DataFrame
  lookback: int

  return dataframe: With the days as index and the amount of engagements and unique users in the
  range=(day - lookback : day). The dataset also has the mean, quantile25 and quantile 75 per day.
  """
  #Select two columns
  prueba1 = engagement_list[['UserId','EventDateTime']]
  #Group by UserId and EventDateTime, the result of size is set as Interacciones
  df_grouped = prueba1.groupby(['UserId', 'EventDateTime']).size().reset_index(name='Interacciones')
  #Return reshaped DataFrame organized by given index / column values.
  df_pivoted = df_grouped.pivot(index='EventDateTime', columns='UserId', values='Interacciones')
  #Fill na and sum values in a rolling window calculations
  #window is lookback
  df_rolling = df_pivoted.fillna(0).rolling(window=lookback).sum()
  #Calculations
  df_rolling['Mean'] = df_rolling[df_rolling !=0].mean(axis=1)
  df_rolling['Quantile_25'] = df_rolling[df_rolling !=0].quantile(q=0.25, axis=1, interpolation='nearest')
  df_rolling['Quantile_75'] = df_rolling[df_rolling !=0].quantile(q=0.75, axis=1, interpolation='nearest')
  
  #pivot to normal dataframe (without multi index in columns )
  df_rolling = pd.DataFrame(df_rolling.to_records())
  #columns with UserId
  columnas_userId = df_rolling.columns[1: -3]
  #drop columns of UserId
  df_rolling = df_rolling.loc[:, ~df_rolling.columns.isin(columnas_userId)]
  
  return df_rolling