import html as html
import pandas as pd
from tkinter import filedialog as fd
import tkinter as tk
import tkinter.messagebox
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.express as px
import dash
import numpy as np
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
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
    data = calc_time_to_scan(
        drop_unlikely_sah(
            select_likely_sah(
                open_file(

                ))))
    return data


def calc_rolling_mean(df):
    # Convert the 'Time to Scan' column to timedelta64[ns] in seconds
    df['Time to Scan'] = pd.to_timedelta(df['Time to Scan'])
    df['Time to Scan'] = df['Time to Scan'].dt.total_seconds()

    # Convert the 'Time to Scan' column to a numeric data type.
    df['Time to Scan'] = pd.to_numeric(df['Time to Scan'], errors='coerce')

    # Filter out rows where 'Time to Scan' is greater than 24 hours.
    df = df[df['Time to Scan'] <= 86400]

    # Resample the data to monthly intervals and calculate the mean of 'Time to Scan' for each month.
    monthly_mean = df.resample('2W', on='Arrival_Date_Time')['Time to Scan'].mean()

    # Calculate the rolling mean of 'Time to Scan' with a window of 4 months.
    rolling_mean = monthly_mean.rolling(window=2).mean()

    # Convert the rolling mean values to hours as a decimal.
    rmh = rolling_mean / 3600

    return rmh


# read data from Excel file
df = create_dataset()
rolling_mean_hours = calc_rolling_mean(df)

# Dash

app = Dash(__name__)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

fig = px.line(x=rolling_mean_hours.index, y=rolling_mean_hours, title="How long do potential SAH patients wait from "
                                                                      "arrival to CT "
                                                                      "scan?",).update_layout(
    xaxis_title="Date", yaxis_title="average time to scan (hours)"
)

intervention_date = pd.to_datetime('2023-03-16')
fig.add_shape(type='line',
              x0=intervention_date, y0=0, x1=intervention_date, y1=1, yref='paper',
              line=dict(color='red', dash='dash'))
fig.add_annotation(x=intervention_date, y=max(rolling_mean_hours),
                   text='Intervention 1',
                   showarrow=True,
                   arrowhead=1,
                   arrowcolor=colors['text'],
                   arrowwidth=2)
fig.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text'])

app.layout = html.Div(children=[
    html.H1(children='SAH QIP Dashboard'),

    html.Div(children='''
        SAH Dashboard: Interactive dashboard for the SAH QIP project.
    '''),

    dcc.Graph(
        id='Moving average of time to CT from arrival',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
