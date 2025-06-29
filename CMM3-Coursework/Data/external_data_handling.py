"""
External Data Handling Module

This module provides functionality to collect and preprocess data required for the Heat Pump Simulation application. 
It includes methods to fetch weather data using the Meteostat API and to parse YAML configuration files.

Global Functions:
- `getYAML`: Reads and parses a YAML configuration file into a dictionary.

Classes:
- 'InputValues'
- 'AmbientTempData'
- 'ManufacturerData'

Dependencies:
- `pandas`: For handling data in tabular format.
- `numpy`: For numerical operations.
- `yaml`: For parsing YAML files.
- `meteostat`: For retrieving historical weather data.
- `datetime`: For managing date and time inputs.
"""


from datetime import datetime
from meteostat import Hourly, Point
import os
import pandas as pd
import numpy as np
import yaml
from scipy.optimize import curve_fit
from scipy.interpolate import PchipInterpolator
from Simulator import formulae


def getYAML(file_name):
    """
    Reads and parses a YAML configuration file into a Python dictionary.

    Args:
        fileName (str): The path to the YAML file.

    Returns:
        dict: Parsed YAML data as a dictionary.

    Raises:
        Exception: If there is an error reading or parsing the YAML file.
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, file_name)  # Create the full path
        
        # Open and load the YAML file into a dictionary
        with open(file_path, 'r') as file:
            input_dict = yaml.safe_load(file)
        return input_dict

    except Exception as e:
        # Print an error message if the YAML file cannot be loaded
        print(f"Error occurred when collecting data from YAML file: {e}")


class InputValues:
    def __init__(self, input_name):
        # Get the directory of the current script (where ManufacturerCOP is defined)
        self.input_name = input_name
        self.data = None
        
    def load_data(self):
        self.data = getYAML(self.input_name)
        
    def value(self, ValueType, ValueName):
        # Check if the data is loaded
        if self.data is None:
            raise ValueError("Input Data not Loaded")
    
        # Check if the ValueType exists
        if ValueType not in self.data:
            raise KeyError(f"ValueType '{ValueType}' not found in input data")
    
        # Check if the ValueName exists within the ValueType
        if ValueName not in self.data[ValueType]:
            raise KeyError(f"ValueName '{ValueName}' not found in '{ValueType}'")
    
        # Return the "value" field
        return self.data[ValueType][ValueName].get("value", None)
   
    def change_input_value(self, ValueType, ValueName, newValue): #Changing the held value not the one stored in inputs.yaml
        self.data[ValueType][ValueName]["value"] = newValue

class AmbientTempData:
    def __init__(self):
        self.location = None
        
        self.start_time = None
        self.end_time = None
        
        self.meteostat_data = None
        self.interpolated_data = None
    
    def set_location(self, location):
        Xloc, Yloc = location
        self.location = Point(Xloc, Yloc)
        
    def set_start_time(self, Year, Month, Day, Hour):
        self.start_time = datetime(Year, Month, Day, Hour)
        
    def set_end_time(self, Year, Month, Day, Hour):
        self.end_time = datetime(Year, Month, Day, Hour)
    
    def import_meteostat_data(self):
        """
        Fetches hourly temperature data for a specified location and time range using the Meteostat API.

        Returns:
            pd.DataFrame: DataFrame containing hourly temperature data with columns:
                          - `temp` (temperature in Kelvin),
                          - `time` (timestamps),
                          - `hours` (elapsed hours from the start of the data).

        Raises:
            ValueError: If location, start time, or end time are not set.
            Exception: If there is an error fetching data from the Meteostat API.
        """
        if self.location is None:
            raise ValueError("Location value not set")
        if self.start_time is None:
            raise ValueError("No start time set")
        if self.end_time is None:
            raise ValueError("No end time set")
        
        try:
            # Fetch hourly weather data for the specified location and time range
            self.meteostat_data = Hourly(self.location, self.start_time, self.end_time).fetch()

            # Add a 'hours' column representing elapsed time in hours
            self.meteostat_data['hours'] = np.arange(len(self.meteostat_data))

            # Convert temperature from Celsius to Kelvin
            self.meteostat_data['temp'] = self.meteostat_data['temp'] + 273.15

            # Drop unnecessary columns for the simulation
            self.meteostat_data = self.meteostat_data.drop(['dwpt', 'rhum', 'prcp', 'snow', 'wdir', 'wspd', 'wpgt', 'pres', 'tsun', 'coco'], axis=1)

        except Exception as e:
            # Print an error message and return an empty DataFrame in case of failure
            print(f"Error fetching Meteostat data: {e}")
            self.meteostat_data = pd.DataFrame()
    
    def interpolate_data(self):
        """
        Sets up an interpolator for temperature data based on Meteostat data.
    
        Args:
            MeteostatData (pd.DataFrame): DataFrame containing hourly outdoor temperature data.
    
        Returns:
            function: An interpolator function that estimates temperature at any time.
    
        Behavior:
            - Uses `PchipInterpolator` for smooth interpolation of temperature data.
            - Interpolates temperature based on the `time` index of the DataFrame.
        """
        if self.meteostat_data is None:
            raise ValueError("Meteostat data not imported")
            
        try:
            # Extract time and temperature data
            times = self.meteostat_data.index.values
            temps = self.meteostat_data['temp'].values
    
            # Create and return the interpolator function
            self.interpolated_data = PchipInterpolator(times, temps)
    
        except Exception as e:
            print(f"Error creating temperature interpolator: {e}")
    
    def get_ambient_temps(self):
        AmbientTempData.import_meteostat_data(self)
        AmbientTempData.interpolate_data(self)
        
        # Returns interpolator of temp data to main script
        return self.interpolated_data

class ManufacturerCOP:
    def __init__(self, file_name):
        self.file_name = file_name
        self.fit_a = None
        self.fit_b = None
        self.std_error = None
    
    def get_cop_parameters(self, condenserTemp):
        """
        Fits manufacturer-provided data to calculate COP parameters for the heat pump.
    
        Args:
            manufacturerCOP (str): Path to the YAML file containing COP data.
            condenserTemp (float): Fixed condenser temperature in Kelvin.
    
        Returns:
            tuple: 
                - fit_a (float): Fitted parameter 'a' for the COP model.
                - fit_b (float): Fitted parameter 'b' for the COP model.
                - std_error (float): Standard error of the fit.
    
        Raises:
            Exception: If there is an error loading or processing the COP data.
    
        Behavior:
            - Reads manufacturer-provided COP data from a YAML file.
            - Computes delta T (temperature difference between condenser and outdoor temperatures).
            - Fits the COP data to a mathematical model using `curve_fit`.
            - Returns the fitted parameters and standard error of the fit.
        """
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, self.file_name)  # Create the full path
            
            # Load COP data from the specified YAML file
            with open(file_path, 'r') as file:
                cop_data = yaml.safe_load(file)
    
            # Convert COP data to a DataFrame
            cop_df = pd.DataFrame(cop_data['heat_pump_cop_data'])
    
            # Calculate delta T (condenser temperature minus outdoor temperature)
            cop_df['delta_T'] = (condenserTemp - 273.15) - cop_df['outdoor_temp_C']
    
            # Prepare data for curve fitting
            deltaT = cop_df['delta_T'].to_numpy()
            copNoisy = cop_df['COP_noisy'].to_numpy()
    
            # Fit the COP model to the noisy COP data
            parameters, covariance = curve_fit(formulae.COP, deltaT, copNoisy)
            self.fit_a, self.fit_b = parameters  # Extract fitted parameters
    
            # Calculate the standard error of the fit
            self.std_error = np.sqrt(np.diag(covariance)).mean()
    
    
        except Exception as e:
            print(f"Error calculating COP parameters: {e}")
        