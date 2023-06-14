import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import base64
import math

from functions.functions_data import get_global_daily, get_rolling, get_rolling_values
from functions.functions_graphics import plot_engagements_users, plot_metrics
from functions.functions_data import get_engagement_list_v2
#Set title, icon, and layout
st.set_page_config(
     page_title="FinHabits",
     page_icon="guitar",
     layout="wide")

#function to load data
@st.cache_data()
def load_data():
    #read the data
    path_to_csv = "data/data_20230606.csv"
    df = pd.read_csv(path_to_csv)
    #change data type
    df['EventDateTime'] = pd.to_datetime(df['EventDateTime'], infer_datetime_format=True, format='mixed')

    #Abreviaturas de los estados de USA
    df_states = pd.read_csv("data/abreviaturas_USA.csv")

    return df, df_states

@st.cache_data()
def convert_df(df):
    return df.to_csv().encode('utf-8')


#load data and create a copy
df, df_states = load_data()
df_filter = df.copy()

#tabs 
tab1, tab2 = st.tabs(["Engagements users", "Engagements Metrics"])

#bins of age
age_bins = {
   "18-29" : (18,29), 
   "30-39" : (30,39),
   "40-49" : (40,49),
   "50-59" : (50,59),
   "60-69" : (60,69),
   "70-79" : (70,79)
}

#diccionario, abreviatura : state
#'Alabama' : 'AL'
df_states = df_states[df_states["Abreviatura"].isin(df.UserState.unique())]
diccionario_abreviaturas = pd.Series(df_states.Abreviatura.values,index=df_states.State).to_dict()

#gender list for the selectbox
gender_list = df[df.UserGender.notna()].UserGender.unique()

#UserMaritalStatus list for the selectbox
maritalstatus_list = df[df.UserMaritalStatus.notna()].UserMaritalStatus.unique()

max_date = pd.to_datetime(df.EventDateTime.max())
min_date = pd.to_datetime(df.EventDateTime.min())
#paginacion del df
def paginate_dataframe(dataframe, page_size = 10, page_num = 1):
    #cuantos resultados por pagina 
    page_size = page_size

    offset = page_size*(page_num-1)

    return dataframe[offset:offset + page_size]

#valores por default 
if "sd" not in st.session_state:
    st.session_state["min_date"] = dt.date(min_date.year, min_date.month,min_date.day)

if "en" not in st.session_state:
    st.session_state["max_date"] = dt.date(max_date.year, max_date.month,max_date.day)

if "rq" not in st.session_state:
    st.session_state["rolling"] = 7

if "age" not in st.session_state:
    st.session_state["index_age"] = 0

if "platform" not in st.session_state:
    st.session_state["index_platform"] = 0

if "state" not in st.session_state:
    st.session_state["index_state"] = 0

if "gender" not in st.session_state:
    st.session_state["index_gender"] = 0

if "maritalstatus" not in st.session_state:
    st.session_state["index_maritalstatus"] = 0


#limpiar el form 
def clear_form():
    st.session_state["sd"] = dt.date(min_date.year, min_date.month,min_date.day)
    st.session_state["en"] = dt.date(max_date.year, max_date.month,max_date.day)
    st.session_state["rq"] = 7
    st.session_state["age"] = "All"
    st.session_state["platform"] = "All"
    st.session_state["state"] = "All"
    st.session_state["gender"] = "All"
    st.session_state["maritalstatus"] = "All"

    
#contenedor
# Using "with" notation
with st.sidebar:
    with st.form("form"):
        #year-month-day
        start_date = st.date_input(label='Start date', key="sd", value = st.session_state["min_date"])
        #year-month-day
        end_date = st.date_input(label='End date', key="en", value = st.session_state["max_date"])
        #rolling quantity
        rolling_quantity = st.number_input(label='Rolling Quantity',step=1, key="rq", value = st.session_state["rolling"] )
        #filtros adicionales 
        st.text("Filter")
        filters_text = []
        #Filter to age
        age_filter = st.selectbox( "Age Bins", ("All", "18-29", "30-39","40-49","50-59","60-69","70-79"), key = "age", index = st.session_state["index_age"])
        #filter df
        if age_filter != "All":
            df_filter = df_filter[df_filter['Age'].between( age_bins[age_filter][0], age_bins[age_filter][1] )]
            filters_text.append("Age: " + age_filter ) 
        #Filter to platform     
        platform_filter = st.selectbox( "Platform",("All", "iOS", "Android"), key = "platform", index = st.session_state["index_platform"])
        #filter df
        if platform_filter != "All":
            df_filter = df_filter[df_filter['Mobile_Device'] == platform_filter]
            filters_text.append("Mobile_Device: " + platform_filter ) 

        #Filter to state     
        #Use the key of the diccionary, i mean, the name of the state
        state_filter = st.selectbox( "State",["All",]  + list(diccionario_abreviaturas.keys()), key = "state", index = st.session_state["index_state"])
        #filter df
        if state_filter != "All":
            df_filter = df_filter[df_filter['UserState'] == diccionario_abreviaturas[state_filter]]
            filters_text.append("State: " + state_filter) 

        #Filter to gender     
        gender_filter = st.selectbox( "Gender", ["All",]  + list(gender_list), key = "gender", index = st.session_state["index_gender"])
        #filter df
        if gender_filter != "All":
            df_filter = df_filter[df_filter['UserGender'] == gender_filter]
            filters_text.append("Gender: " + gender_filter) 

        #Filter to marital status     
        maritalStatus_filter = st.selectbox( "Marital status", ["All",]  + list(maritalstatus_list) , key = "maritalstatus", index = st.session_state["index_maritalstatus"])
        if maritalStatus_filter != "All":
            #filter df
            df_filter = df_filter[df_filter['UserMaritalStatus'] == maritalStatus_filter]
            filters_text.append("Marital Status: " + maritalStatus_filter) 

        f1, f2 = st.columns([1, 1])
        # Every form must have a submit button.
        with f1:
            submitted = st.form_submit_button("Submit")
        with f2:
            clear = st.form_submit_button(label="Clear", on_click=clear_form)

    #this data is used in both plots
    engagement_list = get_engagement_list_v2(df = df_filter, start_date= str(start_date), end_data= str(end_date)  )


    #En el primer tab, show the first plot
    with tab1:
        #data for the plot
        global_metrics = get_global_daily(engagement_list)
        rolled = get_rolling(global_metrics,int(rolling_quantity), engagement_list)
        #plot 
        fig = plot_engagements_users(rolled, str(rolling_quantity) +' days')

        #show active filters
        if filters_text:
            st.subheader("With filters")
            for f in filters_text:
                st.write(f)


        #fig.update_layout(height=800)

        #plot in streamlit
        st.plotly_chart(
            fig, 
            theme="streamlit", use_container_width=True, height=800
        )
          
        # Show the first 10 records of the filtered DataFrame
        st.subheader("Filtered Data")

        #paginacion 
        number = st.number_input('Pagina', value=1,min_value=1, max_value=math.ceil(len(engagement_list.index) / 10), step=1)
        #pag 1 de n paginas 
        st.write("Pagina " + str(number) + " de " + str(math.ceil(len(engagement_list.index) / 10)))
        #muestra la tabla 
        st.table(paginate_dataframe(engagement_list[['UserId', 'EventDateTime', 'Language', 
                                 'Age', 'UserState', 'Mobile_Device',
                                'UserGender', 'UserMaritalStatus']], 10, number))

    #The second plot
    with tab2:
        #data for the plot
        rolling = get_rolling_values(engagement_list, rolling_quantity)
        #plot 
        fig2 = plot_metrics(rolling,  str(rolling_quantity) +' days')

        #show active filters
        if filters_text:
            st.subheader("With filters")
            for f in filters_text:
                st.write(f)
                 
        #plot in streamlit
        st.plotly_chart(
            fig2, 
            theme="streamlit", use_container_width=True, height=800
        )
          
        #st.table(engagement_list.head(10))
        
        st.subheader("Filtered Data")
        number = st.number_input('Pagina', value=1,min_value=1, max_value=math.ceil(len(engagement_list.index) / 10), step=1, key = "paginacion_em")

        st.table(paginate_dataframe(engagement_list[['UserId', 'EventDateTime', 'Language', 
                                 'Age', 'UserState', 'Mobile_Device',
                                'UserGender', 'UserMaritalStatus']], 10, number))
 
csv = convert_df(engagement_list)

st.download_button(
    label="Download data as CSV",
    data=csv,
    file_name='data.csv',
    mime='text/csv',
)