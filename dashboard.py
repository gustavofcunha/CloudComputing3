import os
import redis
import streamlit as st
import json
import time
import plotly.graph_objs as go
import pandas as pd
from collections import deque

REDIS_HOST = "192.168.121.48"
REDIS_PORT = 6379
REDIS_KEY = "2020054498-proj3-output"

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

st.title("TP 3 Cloud Computing: Monitoring Dashboard")

st.sidebar.header("Settings")
refresh_rate = st.sidebar.slider("Refresh rate (seconds)", 1, 60, 5)
history_length = st.sidebar.slider("History length (seconds)", 10, 300, 120)

time_history = deque(maxlen=history_length)
cpu_history = {f'cpu{i}': deque(maxlen=history_length) for i in range(8)}
network_history = deque(maxlen=history_length)
memory_cache_history = deque(maxlen=history_length)

def plot_cpu_usage():
    data = []
    for i in range(8):
        trace = go.Scatter(
            x=list(time_history),
            y=list(cpu_history[f'cpu{i}']),
            mode='lines',
            name=f'CPU {i}',
            line=dict(width=2)
        )
        data.append(trace)

    layout = go.Layout(
        title="Average CPU Usage per Core",
        xaxis=dict(title="Time"),
        yaxis=dict(title="CPU Usage (%)"),
        showlegend=True
    )

    fig = go.Figure(data=data, layout=layout)
    st.plotly_chart(fig)

def plot_network_usage():
    trace = go.Scatter(
        x=list(time_history),
        y=list(network_history),
        mode='lines',
        name='Network Egress',
        line=dict(width=2, color='lightgreen')
    )

    layout = go.Layout(
        title="Network Egress Usage",
        xaxis=dict(title="Time"),
        yaxis=dict(title="Percent (%)"),
        showlegend=True
    )

    fig = go.Figure(data=[trace], layout=layout)
    st.plotly_chart(fig)

def plot_memory_cache():
    trace = go.Scatter(
        x=list(time_history),
        y=list(memory_cache_history),
        mode='lines',
        name='Memory Cache',
        line=dict(width=2, color='lightcoral')
    )

    layout = go.Layout(
        title="Memory Cache Usage",
        xaxis=dict(title="Time"),
        yaxis=dict(title="Percent (%)"),
        showlegend=True
    )

    fig = go.Figure(data=[trace], layout=layout)
    st.plotly_chart(fig)

def main():
    placeholder = st.empty()

    while True:
        try:
            data = r.get(REDIS_KEY)
            data = json.loads(data)
            timestamp = time.strftime('%H:%M:%S')

            time_history.append(timestamp)
            for i in range(8):
                cpu_history[f'cpu{i}'].append(data[f'avg-util-cpu{i}-60sec'])
            network_history.append(data['percent-network-egress'])
            memory_cache_history.append(data['percent-memory-caching'])

            data_dict = {
                "Timestamp": [timestamp],
                "Network Egress (%)": [data['percent-network-egress']],
                "Memory Cache (%)": [data['percent-memory-caching']],
            }
            for i in range(8):
                data_dict[f"CPU {i} Usage (%)"] = [data[f'avg-util-cpu{i}-60sec']]

            df = pd.DataFrame(data_dict)

            with placeholder.container():
                st.write(f"Última atualização: {timestamp}")
                st.dataframe(df)

                plot_cpu_usage()
                plot_network_usage()
                plot_memory_cache()

        except Exception as e:
            st.error(f"Ocorreu um erro: {str(e)}")

        time.sleep(refresh_rate)

if __name__ == "__main__":
    main()
