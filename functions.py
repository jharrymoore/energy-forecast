import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict
import streamlit as st
import pandas as pd

pd.options.display.float_format = "{:,.2f}".format

class Tariff:
    def __init__(
        self,
        name: str,
        gas_sc: float,
        elec_sc: float,
        elec_unit: float,
        gas_unit: float,
        price_cap_schedule: List,
        buffer: int,
    ):
        self.name = name
        self.gas_sc = gas_sc
        self.elec_sc = elec_sc
        self.elec_unit = elec_unit
        self.gas_unit = gas_unit
        self.price_cap_schedule = price_cap_schedule
        self.buffer = buffer
        self.monthly_elec_units, self.monthly_gas_units = self.project_unit_prices()
        self.total = 0

    def daily_cost(self, gas_usage: float, elec_usage: float) -> float:
        return self.gas_daily_cost(gas_usage) + self.elec_daily_cost(elec_usage)

    def gas_daily_cost(self, gas_usage: float) -> float:
        return self.gas_sc + self.gas_unit * gas_usage

    def elec_daily_cost(self, elec_usage: float) -> float:
        return self.elec_sc + self.elec_unit * elec_usage

    def period_cost(self, days: int, gas_usage: float, elec_usage: float) -> float:
        # sum total cost over period
        daily_gas = gas_usage / days
        daily_elec = elec_usage / days
        return self.daily_cost(daily_gas, daily_elec) / 100

    def increase_unit_rate(self, frac: float) -> None:
        # update the unit rates
        self.elec_unit += self.elec_unit * frac
        self.gas_unit += self.gas_unit * frac

    def project_unit_prices(self) -> Tuple[List, List]:
        """Incorperate projected 3-monthly price cap rises into forecast

        :return Tuple[List, List]: gas + elec monthly unit charges
        """
        # self.price_cap_schedule contains 3-monthly projected changes in unit charges
        monthly_elec_units = [self.elec_unit for _ in range(12)]
        monthly_gas_units = [self.gas_unit for _ in range(12)]
        for idx, buf in enumerate([0, 3, 6, 9]):
            monthly_elec_units[self.buffer + buf :] = [
                i * self.price_cap_schedule[idx]
                for i in monthly_elec_units[self.buffer + buf :]
            ]
            monthly_gas_units[self.buffer + buf :] = [
                i * self.price_cap_schedule[idx]
                for i in monthly_gas_units[self.buffer + buf :]
            ]
        return monthly_elec_units, monthly_gas_units

    def run_annual_forecast(self, elec_usage: List, gas_usage: List) -> Dict:

        # predict monthly costs
        gas_usage = np.array(gas_usage)
        elec_usage = np.array(elec_usage)
        monthly_elec = []
        monthly_gas = []
        for i in range(12):
            monthly_gas.append(
                self.gas_sc * 30.437 + self.monthly_gas_units[i] * gas_usage[i]
            )
            monthly_elec.append(
                self.elec_sc * 30.437 + self.monthly_elec_units[i] * elec_usage[i]
            )
        monthly_elec = np.array(monthly_elec) / 100
        monthly_gas = np.array(monthly_gas) / 100
        total_gas = np.round(np.sum(monthly_gas), 2)
        total_elec = np.round(np.sum(monthly_elec), 2)
        output_df = pd.DataFrame({"Total annual gas":
            [total_gas],
            "Total annual elec":
            [total_elec],
            "Total annual energy":
            [total_gas + total_elec]}, index=["£"])
        st.table(
            output_df.round(2).T
        )
        self.total_combined = total_elec + total_gas
        self.monthly_gas = monthly_gas
        self.monthly_totals = {"gas": monthly_gas, "elec": monthly_elec}


def generate_tariff(idx):
    
    name=st.text_input("Tariff name:", key=idx)
    elec_sc = st.slider("Electric standing charge", 1.0, 100.0, step=0.01, key=idx)
    gas_sc = st.slider("Gas standing charge", 1.0, 100.0, step=0.01, key=idx)
    elec_unit = st.slider("Elec unit price", 1.0, 100.0, step=0.01, key=idx)
    gas_unit = st.slider("Gas unit price", 1.0, 100.0, step=0.01, key=idx)

    with st.expander('Price cap schedule'):
    
        
        month_1 = st.slider("Review 1", 0.,2.,1., step=0.01, key=idx)
        month_2 = st.slider("Review 2", 0.,2.,1., step=0.01, key=idx)
        month_3 = st.slider("Review 3", 0.,2.,1., step=0.01, key=idx)
        month_4 = st.slider("Review 4", 0.,2.,1., step=0.01, key=idx)
        price_cap_schedule = [month_1, month_2, month_3, month_4]
        price_cap_delay = st.slider("delay price cap changes (months)", 0, 11,0, key=idx)
    

    
    return Tariff(
        name=name,
        elec_sc=elec_sc,
        gas_sc=gas_sc,
        elec_unit=elec_unit,
        gas_unit=gas_unit,
        price_cap_schedule=price_cap_schedule,
        buffer=price_cap_delay,
    ) 

def collect_forecasts(elec, gas, tariff):
    
    tariff.run_annual_forecast(
        elec_usage=[elec / 12 for _ in range(12)],
        gas_usage=[gas / 12 for _ in range(12)],
    ) 
    return tariff

def plot_figure(tariffs: List[Tariff]):
    data = [t.monthly_totals for t in tariffs]
    fig, axes = plt.subplots(1, len(data), figsize=(20, 8), sharey=True)
    
    title = [t.name for t in tariffs]
    for idx, ax in enumerate(axes.flatten()):
        x = [i for i in range(12)]
        plt.xticks(fontsize=16)
        plt.yticks(fontsize=16)
        ax.bar([i - 0.2 for i in x], data[idx]["elec"], width=0.4, label="elec usage")
        ax.bar([i + 0.2 for i in x], data[idx]["gas"], width=0.4, label="gas usage")
        ax.legend(fontsize=14)
        ax.set_title(title[idx], fontsize=22)
        ax.set_ylabel("Monthly cost / £", fontsize=18)
        ax.set_xlabel("Month", fontsize=18)
        
    return fig