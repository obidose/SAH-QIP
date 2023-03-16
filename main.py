import pandas as pd
from tkinter import filedialog as fd
import tkinter as tk
import tkinter.messagebox
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.express as px
import dash
import numpy as np
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


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


# read data from Excel file
df = create_dataset()

# Convert the 'Arrival_Date_Time' column to datetime type if it's not already.
df['Arrival_Date_Time'] = pd.to_datetime(df['Arrival_Date_Time'])

# Convert the 'Time to Scan' column to timedelta64[ns].
df['Time to Scan'] = pd.to_timedelta(df['Time to Scan'])

# Convert the 'Time to Scan' column to seconds.
df['Time to Scan'] = df['Time to Scan'].dt.total_seconds()

# Convert the 'Time to Scan' column to a numeric data type.
df['Time to Scan'] = pd.to_numeric(df['Time to Scan'], errors='coerce')

# Filter out rows where 'Time to Scan' is greater than 24 hours.
df = df[df['Time to Scan'] <= 86400]

# Resample the data to monthly intervals and calculate the mean of 'Time to Scan' for each month.
monthly_mean = df.resample('M', on='Arrival_Date_Time')['Time to Scan'].mean()

# Calculate the rolling mean of 'Time to Scan' with a window of 4 months.
rolling_mean = monthly_mean.rolling(window=4).mean()

# Convert the rolling mean values to hours as a decimal.
rolling_mean_hours = rolling_mean / 3600

# Plot the moving average of 'Time to Scan' each month.
plt.plot(rolling_mean_hours, label='Moving Average')

# Plot the number of scans within 2 hours.
num_scans_2h = df[df['Time to Scan'] <= 7200].resample('M', on='Arrival_Date_Time')['Time to Scan'].count()
plt.plot(num_scans_2h, label='Scans within 2 Hours')

# Plot the number of scans within 4 hours.
num_scans_4h = df[df['Time to Scan'] <= 14400].resample('M', on='Arrival_Date_Time')['Time to Scan'].count()
plt.plot(num_scans_4h, label='Scans within 4 Hours')

# Plot the number of scans within 6 hours.
num_scans_6h = df[df['Time to Scan'] <= 21600].resample('M', on='Arrival_Date_Time')['Time to Scan'].count()
plt.plot(num_scans_6h, label='Scans within 6 Hours')

# Set the plot title and axis labels.
plt.title('Moving Average of Time to Scan Each Month')
plt.xlabel('Month')
plt.ylabel('Number of Scans / Time to Scan (in hours)')

# Show the legend.
plt.legend()

# Show the plot.
plt.show()