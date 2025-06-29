
"""
GUI Main Script

This script initializes and manages the GUI for the Heat Pump Simulation application.
It sets up the main window, tabs, and buttons for interacting with the simulation, 
plotting results, and performing sensitivity analysis.

Modules Used:
- `customtkinter` (ctk): For modern GUI components.
- `matplotlib`: For embedding plots in the GUI.
- `tkinter.messagebox`: For displaying error messages.
- `yaml`: For working with YAML configuration files.
- `subprocess`: To run external scripts for simulation.

Functions:
- Sets up the main window and tabs for simulation and analysis.
- Links GUI actions (e.g., buttons) to their corresponding functions.
- Embeds plots and results into GUI tabs.

"""

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import matplotlib as plt


### Import GUI modules ###
#from .plot_tabs import PlotTabs # Functions for running the simulation and sensitivity analysis.
#from .parameters_tab import ParametersTab

class GUIclass(ctk.CTk):
    def __init__(self, Simulation):
        super().__init__()
        
        self.define_dictionarys()
        self.SimulationObject = Simulation
        
        #### Define window
        self.title("Heat Pump Simulation")  # Set window title
        self.geometry("800x600")  # Smaller window size
        ctk.set_appearance_mode("dark")  # Dark mode for better visibility
        ctk.set_default_color_theme("dark-blue")  # Blue color theme for consistency

       #### Configure grid layout
        self.grid_columnconfigure(0, weight=0)  # Sidebar proportional scaling
        self.grid_columnconfigure(1, weight=3)  # Main content gets more space
        self.grid_rowconfigure(0, weight=1)  # Adjust row space proportionally

       ### Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=10)  # Smaller sidebar width
        self.sidebar_frame.grid(row=0, column=0, rowspan=5, sticky="nsew", padx=10, pady=10)

       ## Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, text="HPSim", font=ctk.CTkFont(size=30, weight="bold")
        )  # Reduced font size
        self.logo_label.grid(row=0, column=0, padx=10, pady=(10, 10))

       ### Graph Tabs
        self.graph_tabs = ctk.CTkTabview(
            self, width=400, height=300, corner_radius=10, fg_color="grey15"
       )   # Smaller graph area
        self.graph_tabs.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        ## Parameter Entry inside sidebar
        self.entry_frame = ctk.CTkFrame(self.sidebar_frame)
        self.entry_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        # P. Entry Title
        self.entry_label = ctk.CTkLabel(self.entry_frame, text="Simulation Parameters:", font=ctk.CTkFont(size=15, weight="bold"))
        self.entry_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # P. Entry Fields
        self.generateParameterFrame()
        
        # DHW Toggle
        self.switch_var = ctk.StringVar(value="off")
        self.toggle_switch = ctk.CTkSwitch(self.entry_frame, text="Simulate DHW", command=self.DHW_switch_event,variable=self.switch_var, onvalue="on", offvalue="off")
        self.toggle_switch.grid(row=10, column=0, sticky="w", padx=10, pady=10)
        
        # Default Options Button
        self.text_button = ctk.CTkButton(self.entry_frame, text="Set Default Parameters" ,command=self.default_params_button, fg_color="gray29", text_color="white", hover_color="grey41", border_color="black")
        self.text_button.grid(row=10, column=1, sticky="e", padx=10, pady=10)

        ## Run button
        self.text_button = ctk.CTkButton(self.sidebar_frame, text="Run Simulation", command=self.run_simulation, fg_color="green")
        self.text_button.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        
        ## Simulation Results Label
        self.simulation_complete_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Simulation Complete ✓",
            text_color="green",
            font=("Arial", 14)
        )
        self.simulation_complete_label.grid(row=4, column=0, columnspan=2, pady=10)
        self.simulation_complete_label.grid_remove()  # Hide label initially    
        
        
        
        self.graph_canvases = {}
        self.figures = {}
        
        for tab_name, (json_name, displaytype) in self.all_tabs.items():
            tab = self.graph_tabs.add(tab_name)
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)
            
            if displaytype == "plot":
                # Create a matplotlib figure for each tab
                figure = Figure(figsize=(8, 7), dpi=100)
                ax = figure.add_subplot(111)
                ax.set_title(tab_name)
                figure.patch.set_facecolor("#2e2e2e")  # Match CustomTkinter theme
                ax.set_facecolor("#1e1e1e")            # Dark axes background
                ax.spines['top'].set_color("white")
                ax.spines['right'].set_color("white")
                ax.spines['bottom'].set_color("white")
                ax.spines['left'].set_color("white")
                ax.tick_params(colors="white")       # White ticks
                ax.title.set_color("white")          # White title
                ax.xaxis.label.set_color("white")    # White x-axis label
                ax.yaxis.label.set_color("white")    # White y-axis label
                ax.grid(color="gray", linestyle="-", linewidth=1)  # Light grid
                ax.plot([], [])  # Empty plot initially
                
                # Embed the figure in the tab
                canvas = FigureCanvasTkAgg(figure, tab)
                canvas_widget = canvas.get_tk_widget()
                canvas_widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
                
                # Store references for later updates
                self.figures[tab_name] = figure
                self.graph_canvases[tab_name] = canvas

        
        self.graph_tabs.tab("Tank Temperature").grid_columnconfigure(0, weight=1) 
        
        self.loaded_tabs = set() # Tracks tabs loaded
        
        ### Sensitivity Analysis
        self.analysis_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="grey12")
        self.analysis_frame.grid(row=1, column=1, padx=(30, 30), pady=(5, 20), sticky="nsew")

        # Analysis Label
        self.analysis_label = ctk.CTkLabel(
        self.analysis_frame,
        text="Sensitivity Analysis",
        font=ctk.CTkFont(size=16),
        fg_color="grey25",
        corner_radius=5,
        padx=700,
        pady=9,
        anchor="center"
        )
        self.analysis_label.grid(row=0, column=0, columnspan=2, sticky="nw", padx=5, pady=5)
        
        # Parameter Dropdown (to select the variable for sensitivity analysis)
        self.sensitivity_parameter = ctk.StringVar()
        self.sensitivity_dropdown = ctk.CTkOptionMenu(
            self.analysis_frame,
            variable=self.sensitivity_parameter,
            values=list(self.parameter_map.keys()),  # Dropdown values based on parameter keys
            fg_color="grey25"
        )
        self.sensitivity_dropdown.grid(row=1, column=0, padx=10, pady=10)
        
        # Range Entry
        self.range_entry = ctk.CTkEntry(
            self.analysis_frame,
            placeholder_text="Enter range (e.g., 10,20)",
            fg_color="grey25"
        )
        self.range_entry.grid(row=2, column=0, padx=10, pady=10)
        
        # Increment Entry
        self.increment_entry = ctk.CTkEntry(
            self.analysis_frame,
            placeholder_text="Number of Increments",
            fg_color="grey25"
        )
        self.increment_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # Run Sensitivity Analysis Button
        self.sensitivity_button = ctk.CTkButton(
        self.analysis_frame,
        text="Run Sensitivity Analysis",
        command=self.run_sensitivity_analysis,
        fg_color="green"
        )
        self.sensitivity_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)
    
    def update_graph(self):
        """Update the graph based on the selected tab."""
        # Update the graphs in each tab
        
        with open("./Data/simulation_results.json", "r") as file:
            data = json.load(file)

        # Extract shared time data
        time = data["time"]
        for tab_name, (json_name, displaytype) in self.all_tabs.items():
            if displaytype == "plot":
                figure = self.figures[tab_name]
                figure.patch.set_facecolor("#2e2e2e")  # Match CustomTkinter theme
                ax = figure.gca()
                ax.clear()  # Clear the previous plot
                
                # Example: Plot a sine wave with random frequency
                x = time
                y = data[json_name]
                ax.plot(x, y, label=f"{tab_name} data")
                ax.legend()
                ax.set_title(tab_name)
                ax.set_facecolor("#1e1e1e")            # Dark axes background
                ax.spines['top'].set_color("white")
                ax.spines['right'].set_color("white")
                ax.spines['bottom'].set_color("white")
                ax.spines['left'].set_color("white")
                ax.tick_params(colors="white")       # White ticks
                ax.title.set_color("white")          # White title
                ax.xaxis.label.set_color("white")    # White x-axis label
                ax.yaxis.label.set_color("white")    # White y-axis label
                ax.grid(color="gray", linestyle="-", linewidth=1)  # Light grid
                
                # Refresh the canvas
                self.graph_canvases[tab_name].draw()
            else:
                print(tab_name)
                tab = self.graph_tabs.tab(tab_name)
                # Clear existing widgets in the frame
                for widget in tab.winfo_children():
                    widget.destroy()

                if tab_name == "Total Energy Consumption":
                    units = "kJ"
                elif tab_name == "Heat Pump Maximum Thermal Output":
                    units = "W"
                else:
                    units = "%"

                # Format and display the metric
                divide_by=1
                metric_value = data[json_name] / divide_by
                value = f"{metric_value:.2f}"
                title_label = ctk.CTkLabel(tab, text=tab_name, font=("Arial Bold", 18))
                title_label.pack(pady=(10, 5))
        
                value_label = ctk.CTkLabel(tab, text=f"{value} {units}", font=("Arial", 16))
                value_label.pack(pady=(0, 10))
    
    def DHW_switch_event(self):
        if self.switch_var.get() == "on":
            self.SimulationObject.changeDHW(True)
        else:
            self.SimulationObject.changeDHW(False)
    
    def generateParameterFrame(self):
        """Generate input fields for parameters."""
        
        input_fields = {
            ("building_properties", "indoor_setpoint_temperature_K"): "Indoor Temperature Set Point (°C):",
            ("heat_pump", "off_temperature_threshold_K"): "Heat Pump Off Threshold (°C):",
            ("heat_pump", "on_temperature_threshold_K"): "Heat Pump On Threshold (°C):",
            ("initial_conditions", "initial_tank_temperature_K"): "Initial Tank Temperature (°C):",
            ("building_properties", "roof_U_value"): "Roof U-value (W/m²K):",
            ("building_properties", "wall_U_value"): "Wall U-value (W/m²K):",
            ("building_properties", "roof_area"): "Roof Area (m²):",
            ("building_properties", "wall_area"): "Wall Area (m²):",
            ("hot_water_tank", "mass_of_water"): "Tank Water Mass (kg):"
        }
        
        self.entries = {}
        self.param_labels = {}
        
        for number, (key_tuple, label) in enumerate(input_fields.items()):
            self.param_labels[key_tuple] = ctk.CTkLabel(self.entry_frame, text=label)
            self.param_labels[key_tuple].grid(row=number+1, column=0, sticky="e", padx=(20,2), pady=5)
            
            self.entries[key_tuple] = ctk.CTkEntry(self.entry_frame)
            self.entries[key_tuple].grid(row=number+1, column=1, sticky="ew", padx=20, pady=5)
        
    def default_params_button(self):
       """Set default parameters."""
       defaults = {
           ("building_properties", "indoor_setpoint_temperature_K"): 20, 
           ("building_properties", "roof_U_value"): 0.18,
           ("building_properties", "roof_area"): 120,
           ("building_properties", "wall_U_value"): 0.51,
           ("building_properties", "wall_area"): 132,
           ("hot_water_tank", "mass_of_water"): 200,
           ("initial_conditions", "initial_tank_temperature_K"): 45,
           ("heat_pump", "on_temperature_threshold_K"): 40,
           ("heat_pump", "off_temperature_threshold_K"): 60
       }
       
       for key, value in defaults.items():
           self.entries[key].delete(0, "end")
           self.entries[key].insert(0, str(value))
       
       print("Default parameters set.")
       
    def run_simulation(self):
        """Run simulation (placeholder function)."""
        print("Simulation running...")
        for (ValueType, ValueName), entry in self.entries.items():
            try:
               # Convert input to float (or modify based on expected type)
               value = float(entry.get())
               if ValueName in ("initial_tank_temperature_K","off_temperature_threshold_K","on_temperature_threshold_K","indoor_setpoint_temperature_K") :
                   value = value + 273.15 # This parameter is collected in celcius but stored in Kelvin so must be converted
               
                # Assign to the Simulation object
               self.SimulationObject.inputValues.change_input_value(ValueType, ValueName, value)
            except ValueError:
                # Handle invalid inputs gracefully
                print(f"Invalid value for {ValueName}: {entry.get()}")
                continue 
        
        
        self.SimulationObject.simulate()
        self.update_graph()
        self.simulation_complete_label.grid()
        self.after(5000, self.simulation_complete_label.grid_remove)
        
    def run_sensitivity_analysis(self):
        """Run sensitivity analysis and display results."""
        
        param = self.sensitivity_parameter.get()
        if not param:
            raise ValueError("Select a parameter for analysis.")
            
        range_values = self.range_entry.get().split(",")
        increments = int(self.increment_entry.get())
        lower, upper = float(range_values[0]), float(range_values[1])

        step = (upper - lower) / (increments - 1)
        results = []

        for i in range(increments):
            value = lower + i * step
            # Set parameter value in simulation (dummy results for demonstration)
            results.append((value, value * 1.2))  # Example result calculation

            self.display_bar_chart(self.analysis_frame, results, param)
       

    def display_bar_chart(self, frame, results, param_name):
    
       
           # Validate results
        if not results or not all(len(r) == 2 for r in results):
                raise ValueError("Results must be a list of (value, metric) tuples.")
            
            # Clear existing widgets in the frame
        for widget in frame.winfo_children():
            widget.destroy()
            
            # Prepare data
            values, metrics = zip(*[(float(v), float(m)) for v, m in results])
            
            # Create the bar chart
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(values, metrics, color="blue", alpha=0.7)
            ax.set_xlabel(param_name)
            ax.set_ylabel("Metric Value")
            ax.set_title(f"Sensitivity Analysis: {param_name}")
            
            # Embed the chart in the GUI
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(fill="both", expand=True)
            canvas.draw()
       


    def close_window(self):
        self.quit()  # Quit the mainloop when the window is closed
        self.destroy()  # Destroy the window
 
    def define_dictionarys(self): #Put here so that it's at the bottom as it takes up lots of space, making class more readable.
        self.all_tabs = {
            "Tank Temperature": ("temperature","plot"),
            "Heat Load": ("heat_load","plot"),
            "Heat Loss": ("heat_loss", "plot"),
            "COP": ("COP", "plot"),
            "Power Consumption": ("Power consumption", "plot"),
            "Total Energy Consumption": ("Total Energy Consumption","value"),
            "Heat Pump Maximum Thermal Output": ("Heat pump maximum output","value"),
            "Total System Efficiency": ("Total system efficiency","value")
        }
        self.parameter_map = {
            "indoor_temp": {
                "name": "Indoor Temperature Set Point", 
                "path": ["building_properties", "indoor_setpoint_temperature_K", "value"], 
                "is_temp": True
            },
            "roof_u_value": {
                "name": "Roof U-value", 
                "path": ["building_properties", "roof_U_value", "value"]
            },
            "roof_area": {
                "name": "Roof Area", 
                "path": ["building_properties", "roof_area", "value"]
            },
            "wall_u_value": {
                "name": "Wall U-value", 
                "path": ["building_properties", "wall_U_value", "value"]
            },
            "wall_area": {
                "name": "Wall Area", 
                "path": ["building_properties", "wall_area", "value"]
            },
            "tank_mass": {
                "name": "Tank Water Mass", 
                "path": ["hot_water_tank", "mass_of_water", "value"]
            },
            "initial_temp": {
                "name": "Initial Tank Temperature", 
                "path": ["initial_conditions", "initial_tank_temperature_K", "value"], 
                "is_temp": True
            },
            "on_threshold": {
                "name": "Heat Pump On Threshold", 
                "path": ["heat_pump", "on_temperature_threshold_K", "value"], 
                "is_temp": True
            },
            "off_threshold": {
                "name": "Heat Pump Off Threshold", 
                "path": ["heat_pump", "off_temperature_threshold_K", "value"], 
                "is_temp": True
            }
        }
        
        
        

#GUI = GUI()
#GUI.mainloop()

