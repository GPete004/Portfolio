
"""
Domestic Hot Water (DHW) Simulation Module

This module simulates the impact of stochastic DHW draw-off events on tank temperature dynamics.
It generates a DHW flow profile and calculates the resulting heat loss using the Euler method.

Functions:
- `generate_dhw_profile`: Creates a stochastic DHW draw-off profile.
- `Euler_TankDynamicsDHW`: Solves tank dynamics including DHW effects using the Euler method.

Dependencies:
- `numpy`: Numerical operations.
- `pandas`: Time-series handling.
- `matplotlib.pyplot`: Plotting for data visualization.
- `formulae`: Module for scientific calculations like Qload, Qloss, and Qtransfer.

"""

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

class DHW:
    # ============================================
    #        Generate DHW Draw-Off Profile
    # ============================================
    def dhw_profile(duration=24, time_step=60):
        """
        Generates a stochastic DHW draw-off profile for a given duration.
    
        Args:
            duration (int): Duration of the simulation in hours.
            time_step (int): Time step for the simulation in seconds.
    
        Returns:
            pd.Series: A time series of DHW flow rates (kg/s).
        """
        np.random.seed(42)  # Set seed for reproducibility
        total_steps = int(duration * 3600 / time_step)  # Calculate the total number of time steps
        times = np.arange(0, duration * 3600, time_step)  # Time in seconds for the entire duration
        profile = np.zeros(total_steps)  # Initialize flow rate profile with zeros
    
        # Generate number of DHW events using a Poisson distribution
        num_events = np.random.poisson(5)  # Average of 5 events/day
    
        for _ in range(num_events):
            # Randomize event start time (morning and evening peaks)
            if np.random.rand() > 0.5:
                start_time = np.random.normal(loc=7 * 3600, scale=3600)  # Morning peak (~7am)
            else:
                start_time = np.random.normal(loc=19 * 3600, scale=3600)  # Evening peak (~7pm)
    
            # Randomize event duration (exponentially distributed)
            duration = np.random.exponential(scale=300)  # Average duration = 5 min
    
            # Randomize flow rate for the event (uniform distribution)
            flow_rate = np.random.uniform(0.3, 0.5)  # Flow rate range: 0.3 to 0.5 kg/s
    
            # Add event to the profile
            start_index = int(start_time / time_step)
            end_index = int((start_time + duration) / time_step)
            profile[start_index:end_index] += flow_rate
    
        # Create a Pandas Series for better handling
        return pd.Series(profile, index=times)
    
    def dhw_profile_interpolator(profile):
        DHW_interp = PchipInterpolator(profile.index / 3600, profile.values)
        return DHW_interp
    
    def get_dhw_profile():
        profile = DHW.dhw_profile()
        interp = DHW.dhw_profile_interpolator(profile)
        return interp