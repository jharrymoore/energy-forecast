import streamlit as st
from functions import collect_forecasts, generate_tariff, plot_figure

st.title("UK energy forcast")

electricity_usage = st.sidebar.slider('Annual electricity units', 1000, 8000, step=1)
gas_usage = st.sidebar.slider('Annual gas units', 5000, 20000, step=1)

cols = st.columns(2)
all_data = []
for idx, col in enumerate(cols):
    with col:
        tariff = generate_tariff(idx)

        data = collect_forecasts(electricity_usage, gas_usage, tariff)
        all_data.append(data)
fig = plot_figure(all_data)

st.pyplot(fig)



