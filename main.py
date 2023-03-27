import html as html
import pandas as pd
from tkinter import filedialog as fd
import tkinter as tk
import tkinter.messagebox
import plotly.graph_objs as go
import plotly.express as px
from dash import Dash, html, dcc


def open_file():
    df = pd.read_excel("input/input.xlsx", sheet_name="Detail", index_col=0)
    return df


def open_file_gui():
    """Uses a GUI to select a file then returns the content of this file as a dataframe"""
    filename = fd.askopenfilename(title="Select a source file", filetypes=[("Excel Files", "*.xlsx")])
    dataframe1 = pd.read_excel(filename, sheet_name="Detail", index_col=0)
    return dataframe1


def select_likely_sah(df_in):
    """Takes a dataframe, filters results containing CT indication terms likely to suggest ?aneurysmal SAH"""
    df_in['ClinicalIndication'] = df_in['ClinicalIndication'].values.astype(str)
    sah_terms = 'SAH|sudden|subarach|worst|thunderclap|acute|severe|tumour'
    df_out = df_in[df_in["ClinicalIndication"].str.contains(sah_terms, case=False, na=False)]
    return df_out


def drop_unlikely_sah(df_in):
    """Takes a dataframe, filters results containing CT indication terms likely to suggest ?aneurysmal SAH"""
    df_in['ClinicalIndication'] = df_in['ClinicalIndication'].values.astype(str)
    sah_terms = 'week|52|12|month|assault|trauma|injury|shunt|RTC|fall|fell'
    df_out = df_in[df_in["ClinicalIndication"].str.contains(sah_terms, case=False, na=False) == False]
    return df_out


def calc_time_to_scan(df):
    """Works out time to CT scan from hour of arrival in a new column. Also excludes outliers (>24hr)"""
    arrival = pd.to_datetime(df['Arrival_Date_Time'])
    scan = pd.to_datetime(df['ExamStartDateTime'])

    df['Time to Scan'] = scan - arrival

    return df


def export(df):
    """Opens a window to select a save directory. Takes a dataframe and saves it to the selected directory as
    output.xlsx """
    df['Time to Scan'] = df['Time to Scan'].astype('string')
    df.to_excel(fd.askdirectory(title="Select Save Directory") + "/" + "output.xlsx")
    tk.messagebox.showinfo('Save Complete', 'Output saved!')


def create_dataset():
    data = calc_length_of_ip_stay(
        calc_time_to_scan(
            drop_unlikely_sah(
                select_likely_sah(
                    open_file(

                    )))))
    return data


def calc_rolling_mean_hours(df):
    # Convert the 'Time to Scan' column to timedelta64[ns] in seconds
    df['Time to Scan'] = pd.to_timedelta(df['Time to Scan'])
    df['Time to Scan'] = df['Time to Scan'].dt.total_seconds()

    # Convert the 'Time to Scan' column to a numeric data type.
    df['Time to Scan'] = pd.to_numeric(df['Time to Scan'], errors='coerce')

    # Filter out rows where 'Time to Scan' is greater than 24 hours.
    df = df[df['Time to Scan'] <= 86400]

    # Resample the data to 2 week intervals and calculate the mean of 'Time to Scan' for each fortnight.
    fortnight_mean = df.resample('2W', on='Arrival_Date_Time')['Time to Scan'].mean()

    # Calculate the rolling mean of 'Time to Scan' with a window of 2 weeks.
    rolling_mean = fortnight_mean.rolling(window=1).mean()

    # Convert the rolling mean values to hours as a decimal.
    rmh = rolling_mean / 3600

    # # Pending - keep all in df, will need to re-index later graphing
    #     df['Rolling Mean Hours'] = rmh

    return rmh


def calc_length_of_ip_stay(df):
    arrival = pd.to_datetime(df['Arrival_Date_Time'])
    left_hospital = pd.to_datetime(df['IP_Discharge_Date_Time'])

    df['Length_of_IP_Stay'] = left_hospital - arrival

    return df


# read data from Excel file
df = create_dataset()

# Dash

app = Dash(__name__)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

# Fig - Time to CT scan rolling average

intervention_date = pd.to_datetime('2023-03-16')
rolling_mean_hours = calc_rolling_mean_hours(df)
fig = px.line(x=rolling_mean_hours.index,
              y=rolling_mean_hours,
              title="How long do potential SAH patients wait from "
                    "arrival to CT scan? (2 week rolling average)", ).update_layout(
    xaxis_title="Date", yaxis_title="average time to scan (hours)"
)

fig.add_shape(type='line',
              x0=intervention_date, y0=0, x1=intervention_date, y1=1, yref='paper',
              line=dict(color='teal', dash='dash'))
fig.add_annotation(x=intervention_date, y=max(rolling_mean_hours),
                   text='Intervention 1',
                   showarrow=True,
                   arrowhead=1,
                   arrowcolor=colors['text'],
                   arrowwidth=2)
fig.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text'],
    yaxis=dict(range=[0, max(rolling_mean_hours)], gridcolor='grey', zerolinecolor='grey'),
    xaxis=dict(gridcolor='grey', zerolinecolor='grey')
)

# fig2 - Length of ED stay

fig2 = px.line(x=df['Arrival_Date_Time'],
               y=df['LOS'].rolling(window=14).mean(),
               title="Sudden onset, severe headache patients - Length of ED stay (14 Day rolling average)"
               ).update_layout(
    xaxis_title="Date", yaxis_title="Hours"
)

fig2.add_shape(type='line',
               x0=intervention_date, y0=0, x1=intervention_date, y1=1, yref='paper',
               line=dict(color='teal', dash='dash'))
fig2.add_annotation(x=intervention_date, y=30,
                    text='Intervention 1',
                    showarrow=True,
                    arrowhead=1,
                    arrowcolor=colors['text'],
                    arrowwidth=2)
fig2.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text'],
    yaxis=dict(range=[0, 30], gridcolor='grey', zerolinecolor='grey'),
    xaxis=dict(gridcolor='grey', zerolinecolor='grey')
)

# Fig3- Thunderclap patients admitted to med per month

med_patients = df[df['Referral'] == 'ED Referral to Acute Medicine']
med_patients_by_week = med_patients.groupby(pd.Grouper(key='Arrival_Date_Time', freq='MS')).size().reset_index(
    name='count')

fig3 = px.bar(med_patients_by_week,
              x='Arrival_Date_Time',
              y='count',
              title="How many patients with thunderclap headache are admitted to medicine per month?", ).update_layout(
    xaxis_title="Date", yaxis_title="Number of patients admitted"
)

fig3.add_shape(type='line',
               x0=intervention_date, y0=0, x1=intervention_date, y1=1, yref='paper',
               line=dict(color='teal', dash='dash'))
fig3.add_annotation(x=intervention_date, y=max(rolling_mean_hours),
                    text='Intervention 1',
                    showarrow=True,
                    arrowhead=1,
                    arrowcolor=colors['text'],
                    arrowwidth=2)
fig3.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text'],
    yaxis=dict(range=[0, max(rolling_mean_hours)], gridcolor='grey', zerolinecolor='grey'),
    xaxis=dict(gridcolor='grey', zerolinecolor='grey')
)

app.layout = html.Div(children=[
    html.H1(children='SAH QIP Dashboard'),

    html.Div(children='''
        SAH Dashboard: Interactive dashboard for the SAH QIP project.
    '''),

    dcc.Graph(
        id='Moving average of time to CT from arrival',
        figure=fig
    ),

    dcc.Graph(
        id='Length of Stay',
        figure=fig2
    ),

    dcc.Graph(
        id='Number admitted',
        figure=fig3
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
