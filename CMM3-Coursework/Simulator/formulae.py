"""
Scientific Formulae Module

This module contains thermodynamic and scientific calculation functions required by the Heat Pump Simulation application.
It includes calculations for heat pump performance, energy transfers, tank dimensions, and heat losses.

Functions:
- `COP`: Calculates the Coefficient of Performance for a heat pump.
- `CalculateQload`: Computes the building's heat load based on its properties and ambient temperature.
- `CalculateQtransfer`: Determines the heat transfer rate from the condenser to the tank.
- `CalculateQloss`: Calculates heat loss from the tank to the ambient environment.
- `vol_calc`: Computes the tank volume based on the mass of water.
- `tank_dimension`: Determines the dimensions of the tank given its volume and height-radius ratio.
- `tank_SA`: Calculates the surface area of the tank.
- `calculate_total_energy_consumption`: Computes total energy consumed over time.
- `calculate_total_heat_transfer`: Computes total heat transfer energy over time.
- `calculate_total_heat_loss`: Computes total heat loss over time.
- `calculate_total_eff`: Computes the total system efficiency.
- `Qmax`: Determines the maximum heat output of the heat pump.

Dependencies:
- `math`: For mathematical calculations using PI etc.
- `numpy`: For numerical operations using arrays.
"""

import math

class formulae:
    # =============================== #
    #    Heat Pump Performance       #
    # =============================== #
    
    def COP(deltaT, a, b):
        """
        Calculates the Coefficient of Performance (COP) of the heat pump based on temperature difference.
    
        Args:
            deltaT (float): Temperature difference between condenser and outdoor temperature (K).
            a (float): Fitted parameter from curve fit.
            b (float): Fitted parameter from curve fit.
    
        Returns:
            float: Calculated COP value.
        """
        # COP is modeled as a linear relationship with temperature difference
        return a + (b / deltaT)
    
    
    # =============================== #
    #    Heat Load ,Transfer and loss #
    # =============================== #
    
    def CalculateQload(inputValues, Tamb):
        """
        Calculates the building's heat load.
    
        Args:
            buildingProperties (dict): Dictionary containing wall/roof area, U-values, and indoor setpoint temperature.
            Tamb (float): Ambient outdoor temperature (K).
    
        Returns:
            float: Heat load in watts (W).
        """
        # Extract building properties for walls and roof
        Aw = inputValues.value('building_properties', 'wall_area')
        Uw = inputValues.value('building_properties', 'wall_U_value')
        Ar = inputValues.value('building_properties', 'roof_area')
        Ur = inputValues.value('building_properties', 'roof_U_value')
        Tsp= inputValues.value('building_properties', 'indoor_setpoint_temperature_K')
    
        # Calculate heat load for walls and roof
        Qload = Aw * Uw * (Tamb - Tsp) + Ar * Ur * (Tamb - Tsp)
        return -1*Qload  # Negative sign represents a load on the heating system
    
    
    def CalculateQtransfer(inputValues, Ttank):
        """
        Calculates heat transfer rate from condenser to tank.
    
        Args:
            heatPumpProperties (dict): Contains heat pump properties like U-value, area, and condenser temperature.
            Ttank (float): Temperature of the tank water (K).
    
        Returns:
            float: Heat transfer rate (W).
        """
        # Extract properties from the heat pump
        Ucond = inputValues.value('heat_pump', 'overall_heat_transfer_coefficient')
        Acond = inputValues.value('heat_pump', 'heat_transfer_area')
        Tcond = inputValues.value('heat_pump', 'fixed_condenser_temperature_K')
    
        # Calculate heat transfer rate using the equation Q = U * A * ΔT
        return Ucond * Acond * (Tcond - Ttank)
    
    
    def CalculateQloss(inputValues, Atank, Ttank, Tambient):
        """
        Calculates heat loss from the tank to the ambient environment.
    
        Args:
            Atank (float): Surface area of the tank (m²).
            heatPumpProperties (dict): Contains properties like heat loss coefficient.
            tankProperties (dict): Tank-specific properties.
            Ttank (float): Tank water temperature (K).
            Tambient (float): Ambient temperature (K).
    
        Returns:
            float: Heat loss (W).
        """
        # Extract heat loss coefficient from the tank properties
        Uloss = inputValues.value('hot_water_tank', 'heat_loss_coefficient')
        
        # Calculate heat loss using the equation Q = U * A * ΔT
        return Uloss * Atank * (Ttank - Tambient)
    
    
    # =============================== #
    #    Tank Properties and Geometry #
    # =============================== #
    
    def vol_calc(inputValues):
        """
        Calculates the volume of the tank based on the mass of water.
    
        Args:
            tank_properties (dict): Contains the mass of water in the tank.
    
        Returns:
            float: Volume of the tank (m³).
        """
        # Convert water mass (kg) to volume (m³) using the density of water (1000 kg/m³)
        water_mass = inputValues.value('hot_water_tank', 'mass_of_water')
        
        return water_mass / 1000
    
    
    def tank_dimension(tank_vol, RHratio):
        """
        Computes the tank dimensions based on its volume and height-radius ratio.
    
        Args:
            tank_vol (float): Volume of the tank (m³).
            RHratio (float): Ratio of height to radius.
    
        Returns:
            tuple: Height and radius of the tank (m, m).
        """
        # Calculate radius and height based on volume and ratio
        r = (tank_vol / (math.pi * RHratio)) ** (1 / 3)
        h = RHratio * r
        return h, r
    
    
    def tank_SA(inputValues, RHratio):
        """
        Calculates the surface area of the tank based on its dimensions.
    
        Args:
            tank_properties (dict): Contains tank-specific properties.
            RHratio (float): Ratio of height to radius.
    
        Returns:
            float: Surface area of the tank (m²).
        """
        # Compute tank volume and dimensions
        tank_vol = formulae.vol_calc(inputValues)
        h, r = formulae.tank_dimension(tank_vol, RHratio)
    
        # Calculate surface area as 2πrh + 2πr²
        return 2 * math.pi * r * h + 2 * math.pi * r**2
    
    
    # =============================== #
    #    Energy and Efficiency        #
    # =============================== #
    
    def calculate_total_energy_consumption(Pin_values, time_values):
        """
        Computes total energy consumption over time.
    
        Args:
            Pin_values (array-like): Power input values (W).
            time_values (array-like): Corresponding time values (hours).
    
        Returns:
            float: Total energy consumption (J).
        """
        total_energy = 0
        time_values = time_values * 3600  # Convert hours to seconds
        for i in range(1, len(Pin_values)):
            delta_t = time_values[i] - time_values[i-1]  # Time interval
            energy_step = Pin_values[i] * delta_t  # Energy for this interval
            total_energy += energy_step
        return total_energy
    
    
    def calculate_total_heat_transfer(qtransfer, time_values):
        """
        Computes total heat transfer energy over time.
    
        Args:
            qtransfer (array-like): Heat transfer values (W).
            time_values (array-like): Corresponding time values (hours).
    
        Returns:
            float: Total heat transfer energy (J).
        """
        total_heat_transfer_energy = 0
        time_values = time_values * 3600  # Convert hours to seconds
        for i in range(1, len(qtransfer)):
            delta_t = time_values[i] - time_values[i-1]
            heat_energy_step = qtransfer[i] * delta_t
            total_heat_transfer_energy += heat_energy_step
        return total_heat_transfer_energy
    
    
    def calculate_total_heat_loss(heatloss, time_values):
        """
        Computes total heat loss over time.
    
        Args:
            heatloss (array-like): Heat loss values (W).
            time_values (array-like): Corresponding time values (hours).
    
        Returns:
            float: Total heat loss energy (J).
        """
        total_heat_loss = 0
        time_values = time_values * 3600  # Convert hours to seconds
        for i in range(1, len(heatloss)):
            delta_t = time_values[i] - time_values[i-1]
            heat_energy_loss_step = heatloss[i] * delta_t
            total_heat_loss += heat_energy_loss_step
        return total_heat_loss
    
    
    def calculate_total_eff(total_load, total_qtransfer):
        """
        Computes the total system efficiency.
    
        Args:
            total_load (float): Total heat load (J).
            total_energy (float): Total energy consumption (J).
    
        Returns:
            float: Total efficiency as a fraction.
        """
        return (total_load / total_qtransfer)*100
    
    
    def Qmax(Pin, COP):
        """
        Determines the maximum heat output of the system.
    
        Args:
            Pin (array-like): Power input values (W).
            COP (array-like): Coefficient of Performance values.
    
        Returns:
            float: Maximum heat output (W).
        """
        # Calculate maximum heat output as max(Pin) * max(COP)
        return max(Pin) * max(COP)
