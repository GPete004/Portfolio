from Data import InputValues, AmbientTempData, ManufacturerCOP
from Simulator import simulation
from GUI import GUIclass

# Default data locations
input_file = 'inputs.yaml'
manufacturer_cop_data = 'heat_pump_cop_synthetic_full.yaml'

# Default Simulation Conditions
location = (55.9533, -3.1883)  # Edinburgh latitude and longitude
start_year, start_month, start_day, start_hour = 2023, 10, 30, 0  # Simulation start time
end_year, end_month, end_day, end_hour = 2023, 10, 31, 0  # Simulation end time
condenser_temp_celcius = 65 + 273.15  # Condenser temperature in Kelvin (fixed at 65°C)
RHratio = 2  # Ratio of height to radius for the tank dimensions
DHWsimulation = False # Should the simulation account for domestic hot water draw?

# Initialise input data objects    
input_values = InputValues(input_file)
input_values.load_data()

manufacturer_cop = ManufacturerCOP(manufacturer_cop_data)
manufacturer_cop.get_cop_parameters(condenser_temp_celcius)

ambient_data = AmbientTempData()
ambient_data.set_location(location)
ambient_data.set_start_time(start_year, start_month, start_day, start_hour)
ambient_data.set_end_time(end_year, end_month, end_day, end_hour)

interpolated_data = ambient_data.get_ambient_temps()

# Run Simulation
Simulation = simulation.Simulator(input_values, interpolated_data, manufacturer_cop, RHratio, DHWsimulation)

GUI = GUIclass(Simulation)
GUI.protocol("WM_DELETE_WINDOW", GUI.close_window)
GUI.mainloop()
