import matplotlib.pyplot as plt
import numpy as np

from shiny import *
from functions.functions_data import get_global_daily, get_rolling, get_rolling_values
from functions.functions_graphics import plot_engagements_users, plot_metrics
from functions.functions_data import get_engagement_list_v2
import pandas as pd

from shinywidgets import output_widget, render_widget
#import the data
def load_data():
    #read the data
    path_to_csv = "data/attribution_detected.csv"
    df = pd.read_csv(path_to_csv, parse_dates=['EventDateTime'], dtype={'CurrentPlatform': str,
                                                                        'CurrentType': str,
                                                                        'Platform': str,
                                                                        'Version': str})
    #change data type
    df['EventDateTime'] = pd.to_datetime(df['EventDateTime'])

    #Abreviaturas de los estados de USA
    df_states = pd.read_csv("data/abreviaturas_USA.csv")

    return df, df_states

#call the funcion load_data
df, df_states = load_data()

#quita nan
def remove_nan(df_plot):
  for col in df_plot:
    #get dtype for column
    column_type = df_plot[col].dtype 
    #check if it is a number
    if column_type == int or column_type == float:
        df_plot[col] = df_plot[col].fillna(0)
    else:
        df_plot[col] = df_plot[col].fillna("")
    return df_plot
#create a copy 
df_filter = df.copy()

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

#Pagnacion del df 
def paginate_dataframe(dataframe, page_size = 10, page_num = 1):
    #cuantos resultados por pagina 
    page_size = page_size

    offset = page_size*(page_num-1)

    return dataframe[offset:offset + page_size]

app_ui = ui.page_fluid(
    ui.layout_sidebar(

      ui.panel_sidebar(
        ui.input_date("sd", "Start date", value = min_date),
        ui.input_date("ed", "End date", value = max_date),
        ui.input_numeric("rq", "Rolling Quantity", 7, step=1),
        ui.input_selectize("age", "Age Bins", ("All", "18-29", "30-39","40-49","50-59","60-69","70-79")),
        ui.input_selectize("platform", "Platform",("All", "iOS", "Android")),
        ui.input_selectize("state", "State" , ["All",]  + list(diccionario_abreviaturas.keys())),
        ui.input_selectize("gender", "Gender", ["All",]  + list(gender_list) ),
        ui.input_selectize("maritalstatus", "Marital status", ["All",]  + list(maritalstatus_list) ),
        ui.input_action_button("go", "Submit", class_="btn-success"),
        ui.input_action_button("clean", "Clean", class_="btn btn-primary"),width= 3

        ),
        ui.panel_main(
            ui.navset_tab(
                ui.nav("Engagements users", 
                    output_widget("my_widget")
                 ),
                ui.nav("Engagements Metrics", 
                    output_widget("my_widget_2")
                ),
            ),
            ui.output_text_verbatim("filters"),
            ui.input_numeric("paginacion", "Paginacion", 1, step =1, min=1),
            ui.output_text_verbatim("txt"),
            ui.output_table("engagement_table"),
            ui.download_button("download_data", "Download"),
            )
)
)


def server(input: Inputs, output: Outputs, session: Session):

    @reactive.Calc
    def calc_df():
        filters_text = []
        df_filter = df.copy()
        #filter df
        if input.age() != "All":
            df_filter = df_filter[df_filter['Age'].between( age_bins[input.age()][0], age_bins[input.age()][1] )]
            filters_text.append("Age: " + input.age()  ) 
        #filter df
        if input.platform() != "All":
            df_filter = df_filter[df_filter['Mobile_Device'] == input.platform()]
            filters_text.append("Mobile_Device: " + input.platform() ) 
        #filter df
        if input.state() != "All":
            df_filter = df_filter[df_filter['UserState'] == diccionario_abreviaturas[input.state()]]
            filters_text.append("State: " + input.state()) 
        #filter df
        if input.gender() != "All":
            df_filter = df_filter[df_filter['UserGender'] == input.gender()]
            filters_text.append("Gender: " + input.gender()) 
        #filter df
        if input.maritalstatus() != "All":
            df_filter = df_filter[df_filter['UserMaritalStatus'] == input.maritalstatus()]
            filters_text.append("Marital Status: " + input.maritalstatus() )

        #this data is used in both plots
        engagement_list = get_engagement_list_v2(df = df_filter, start_date= str(input.sd()), end_data= str(input.ed()))
        
        return engagement_list, filters_text

    @output
    @render_widget
    @reactive.event(input.go, ignore_none=False)
    def my_widget():
        engagement_list, filters_text = calc_df()
        #data for the plot
        global_metrics = get_global_daily(engagement_list)
        rolled = get_rolling(global_metrics,int(input.rq()), engagement_list)
        #remove nan, because error "Out of range float values are not JSON compliant"
        rolled = remove_nan(rolled)
        fig = plot_engagements_users(rolled, str(input.rq()) +' days')
        return fig
    
    @output
    @render_widget
    @reactive.event(input.go, ignore_none=False)
    def my_widget_2():
        engagement_list, filters_text = calc_df()
        #data for the plot
        rolling = get_rolling_values(engagement_list, int(input.rq()))[["Mean","Quantile_25", "Quantile_75" ]]
        #remove nan, because error "Out of range float values are not JSON compliant"
        rolling = rolling.fillna(0)

        fig2 = plot_metrics(rolling,  str(input.rq()) +' days')

        return fig2
    
    @output
    @render.text
    @reactive.event(input.go, ignore_none=False)
    def filters():
        titulo = "Filtros: \n"
        engagement_list, filters_text = calc_df()
        if len(filters_text) >= 1:
            filters_text = "\n".join(filters_text)
        else:
            filters_text = "Ninguno"
        return titulo + filters_text
    
    @output
    @render.table
    @reactive.event(input.paginacion, ignore_none=False)
    def engagement_table():
        engagement_list, filters_text = calc_df()

        engagement_list = paginate_dataframe(engagement_list, 10, input.paginacion())
        return engagement_list[['UserId', 'EventDateTime', 'Language', 
                                 'Age', 'UserState', 'Mobile_Device',
                                'UserGender', 'UserMaritalStatus']]
    @output
    @render.text
    @reactive.event(input.paginacion, ignore_none=False)
    def txt():
        engagement_list, filters_text = calc_df()
        texto = "Pagina " + str(input.paginacion()) + " de " + str(len(engagement_list.index))
        return texto
    
    @session.download(filename=f'pan.csv')
    def download_data():
        engagement_list, filters_text = calc_df()
        yield engagement_list.to_csv(index=False)

    

    @reactive.Effect
    @reactive.event(input.clean)
    def _():
        ui.update_date("sd", value = min_date)
        ui.update_date("ed", value = max_date)
        ui.update_numeric("rq", value = 7)
        ui.update_selectize("age", selected="All")
        ui.update_selectize("platform", selected="All")
        ui.update_selectize("state", selected="All")
        ui.update_selectize("gender", selected="All")
        ui.update_selectize("maritalstatus", selected="All")






app = App(app_ui, server)
