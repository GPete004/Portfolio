# CMM3-Coursework
 
## File Structure
**Main.py** Initialises and starts program
**GUI** GUI Scripts
    **GUI.py** Defines GUIclass() to be used as an object in Main.py
**Data** Imported data handling
    **external_data_handling.py** Defines classes for objects containing imported data, allowing it to be updated from anywhere.
**Simulator** ODE Simulation scripts
    **DHW.py** Domestic hot water profile functions
    **formulae.py** Class containing all scientific/mathematical equations used in the script calculations
    **simulation** Defines simulation class and it's functions, holds instances of imported data objects, and use .simulate() from anywhere