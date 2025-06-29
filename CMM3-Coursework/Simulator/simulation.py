"""
Main Simulation Script

This script coordinates the Heat Pump Simulation by collecting inputs, processing data, 
and solving the tank dynamics model using the Euler method. It generates results 
for energy consumption, system efficiency, and heat transfer, saving them to a JSON file.

Modules:
- `formulae`: For scientific calculations like Qload, Qtransfer, Qloss, COP, and efficiency metrics.
- `DataCollection`: Handles weather data collection and YAML input parsing.
- `DataProcessing`: Performs data fitting and interpolation for COP and temperature data.
- `Simulation`: Defines and solves the ODE for tank temperature dynamics.

Inputs:
- YAML file for simulation parameters.
- Meteostat API for outdoor temperature data.
- Manufacturer-provided COP data for the heat pump.

Outputs:
- JSON file (`simulation_results.json`) with simulation results.


"""

# Import necessary modules for Task A of the Heat Pump Simulation project

# Scientific calculations (Qload, Qtransfer, Qloss, COP, etc.)
from .formulae import formulae  
from .DHW import DHW   
import numpy as np               # Numerical operations
import json                      # Save results to a JSON file
import os

class Simulator:
    def __init__(self, inputValues, interpolated_data, manufacturer_cop, RHratio, DHWsimulationBool):
        self.inputValues = inputValues
        self.interpolated_data = interpolated_data
        self.fit_a = manufacturer_cop.fit_a
        self.fit_b = manufacturer_cop.fit_b
        self.RHratio = RHratio
        
        # Simulation Conditions
        
        
        self.simulation_results = None
        self.DHW = DHWsimulationBool # Domestic hot water simulation turned off by default
     
    def euler(self):   
        self.T_off = self.inputValues.value('heat_pump', 'off_temperature_threshold_K')
        self.T_on = self.inputValues.value('heat_pump', 'on_temperature_threshold_K')
        self.total_time = self.inputValues.value('simulation_parameters', 'total_time_seconds')
        self.num_points = self.inputValues.value('simulation_parameters', 'time_points')
        self.time_values = np.linspace(0, self.total_time, self.num_points)
        self.step_size = self.total_time / (self.num_points - 1)
        self.T_inlet = 300 # Default T Inlet for DHW
        
        # Initial Conditions
        self.initial_tank_temp = self.inputValues.value('initial_conditions', 'initial_tank_temperature_K')
        self.initial_pump_status = 'on' if self.initial_tank_temp < self.T_on else 'off'
        
        
        pump_status = self.initial_pump_status
        
        Ttank_values = np.zeros(self.num_points)  # Tank temperature (K)
        cop_values = np.zeros(self.num_points)  # COP values
        heat_load_values = np.zeros(self.num_points)  # Heat load (W)
        heat_loss_values = np.zeros(self.num_points)  # Heat loss (W)
        Pin_values = np.zeros(self.num_points)  # Power input (W)
        Qtransfer_values = np.zeros(self.num_points)  # Heat transfer (W)
        
        if self.DHW:
            dhw_interp_profile = DHW.get_dhw_profile()
            QDHW_values = np.zeros(self.num_points)  # DHW heat loss (W)
            
        
        Atank = formulae.tank_SA(self.inputValues, self.RHratio)
        
        Ttank_values[0] = self.initial_tank_temp
        
        for i in range(1, self.num_points):
            t = self.time_values[i - 1]  # Current time
            Ttank = Ttank_values[i - 1]  # Current tank temperature
    
            # Interpolate ambient temperature
            Tamb = self.interpolated_data(t / 3600)  # Convert time to hours
            
            if self.DHW: 
                mdot_DHW = dhw_interp_profile(t / 3600)
                QDHW = mdot_DHW * 4186 * (Ttank - self.T_inlet)  # DHW heat loss (W)
            else:
                QDHW = 0
    
            # Update pump status based on thresholds
            if Ttank >= self.T_off:
                pump_status = 'off'
            elif Ttank <= self.T_on:
                pump_status = 'on'
    
            # Calculate heat load, transfer, and loss
            Qload = formulae.CalculateQload(self.inputValues, Tamb)
            Qtransfer = formulae.CalculateQtransfer(self.inputValues, Ttank) if pump_status == 'on' else 0
            Qloss = formulae.CalculateQloss(self.inputValues, Atank, Ttank, Tamb)
    
    
            # Calculate COP and power input
            COP = formulae.COP(65 + 273.15 - Tamb, self.fit_a, self.fit_b) if pump_status == 'on' else 0
            Pin = Qtransfer / COP if COP > 0 else 0
    
            # Store values in corresponding arrays
            heat_load_values[i] = Qload
            Qtransfer_values[i] = Qtransfer
            heat_loss_values[i] = Qloss
            cop_values[i] = COP
            Pin_values[i] = Pin
    
            # Update tank temperature using Euler's method
            dTdt = (Qtransfer - Qload - Qloss - QDHW) / self.inputValues.value('hot_water_tank','total_thermal_capacity')
            Ttank_values[i] = Ttank + self.step_size * dTdt
    
        # Convert time to hours for output and data to lists for compatibility with JSON serialization 
        if self.DHW:
            QDHWReturn = QDHW_values.tolist() # DHW heat loss values (W)
        else:
            QDHWReturn = "DHW Simulation Off"
            
        return (    
            (self.time_values / 3600).tolist(),  # Time values in hours
            Ttank_values.tolist(),  # Tank temperatures (K)
            heat_load_values.tolist(),  # Heat load values (W)
            heat_loss_values.tolist(),  # Heat loss values (W)
            cop_values.tolist(),  # COP values
            Pin_values.tolist(),  # Power input values (W)
            Qtransfer_values.tolist(),  # Heat transfer values (W)
            QDHWReturn
            )

    
    def calculate_performance(self, time_values, temperature_values, heat_load_values, heat_loss_values, cop_values, Pin_values, Qtransfer_values):
        # ================================================
        # Calculate Performance Metrics
        # ================================================

        # Calculate total energy consumption (J)
        total_energy = formulae.calculate_total_energy_consumption(Pin_values, time_values)

        # Calculate total heat loss (J)
        #total_qloss = formulae.calculate_total_heat_loss(heat_loss_values, time_values)

        # Calculate total heat transfer (J)
        total_qtransfer = formulae.calculate_total_heat_transfer(Qtransfer_values, time_values)

        # Calculate total heat load (J)
        hl_tot = formulae.calculate_total_heat_loss(heat_load_values, time_values)

        # Calculate total system efficiency
        total_eff = formulae.calculate_total_eff(hl_tot, total_qtransfer)

        # Calculate maximum heat pump output (W)
        max_out = formulae.Qmax(Pin_values, cop_values)
        
        return total_energy, total_eff, max_out
    
    def store_values(self, time_values, temperature_values, heat_load_values, heat_loss_values, cop_values, Pin_values, total_energy, total_eff, max_out, QDHW):
        # Prepare the results dictionary
        results = {
            "time": time_values,  # Convert NumPy array to list for JSON serialization
            "temperature": [temp - 273.15 for temp in temperature_values],  # Convert Kelvin to Celsius
            "heat_load": heat_load_values,
            "heat_loss": heat_loss_values,
            "COP": cop_values,
            "Power consumption": Pin_values,
            "Total Energy Consumption": total_energy,
            "Total system efficiency": total_eff,
            "Heat pump maximum output": max_out,
            "Domestic Hot Water Loss": QDHW
        }
        
        self.current_folder = os.path.dirname(__file__)  # Current file's folder
        self.parent_folder = os.path.abspath(os.path.join(self.current_folder, ".."))  # Parent folder
        target_folder = os.path.join(self.parent_folder, 'Data')
        target_file_path = os.path.join(target_folder, 'simulation_results.json')
        
        # Write results to a JSON file
        with open(target_file_path, "w") as file:
            json.dump(results, file)

        print("Simulation results saved to ../Data/simulation_results.json")

        
    def simulate(self):
        time_values, temperature_values, heat_load_values, heat_loss_values, cop_values, Pin_values, Qtransfer_values, QDHW = Simulator.euler(self)
        total_energy, total_eff, max_out = Simulator.calculate_performance(self, time_values, temperature_values, heat_load_values, heat_loss_values, cop_values, Pin_values, Qtransfer_values)
        Simulator.store_values(self, time_values, temperature_values, heat_load_values, heat_loss_values, cop_values, Pin_values, total_energy, total_eff, max_out, QDHW)
    
    def set_dhw_inlet_temp(self, NewTinlet):
        self.T_inlet = NewTinlet
    
    def changeDHW(self, newValue):
        self.DHW = newValue

