import csv
import timeit
import tkinter as tk
from tkinter import ttk
import tkinter.font as font
from typing import List
import pathlib
import datetime
from otoTests import * 
import ctypes
import datetime
import seaborn as sns  # for graphs
import matplotlib
import globalvars  # anyvariable/funtion you want globally available goes here
import serial
import pyoto.otoProtocol.otoCommands as pyoto
matplotlib.use("Agg")  # needed to prevent multi-thread failures when using matplotlib
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class VacError(Exception):
    pass

class EOLLocationError(Exception):
    pass

class LogFileLocationError(Exception):
    pass

class MainWindow(tk.Tk):
    ProgramVersion = "v0.9α"
    BAD_COLOUR = "#ff6464"
    GOOD_COLOUR = "#10aa10"
    IN_PROCESS_COLOUR = "YELLOW"
    NORMAL_COLOUR = "WHITE"
    SCALEFACTOR = 1  # scale factor is one if there are 1440 vertical pixels on the screen
    FIGSIZEX = 17  # width of chart window for a 2160 vertical pixel screen, to be scaled at the init stage
    FIGSIZEY = 10.7 # height of chart window, for a 2160 vertical pixel screen, to be scaled at the init stage
    DPI = 120  # scale based on monitor dots per inch
    FONTFAMILY = "Consolas"
    
    def __init__(self):
        tk.Tk.__init__(self)
        self.tk.call("tk", "scaling", 1.33)  # needed to prevent graphs from growing during data updates
        self.SCALEFACTOR = 1.0 * self.winfo_screenwidth() / 3840  # scaling based on screen size - sized for 3840 x 2160 screen
        self.FIGSIZEX = self.FIGSIZEX * self.SCALEFACTOR  # scaled width of chart window
        self.FIGSIZEY = self.FIGSIZEY * self.SCALEFACTOR  # scaled height of chart window
        self.CleanOnly = tk.IntVar()
        self.ReplaceParts = tk.IntVar()
        sns.set_theme(font = self.FONTFAMILY, font_scale = 1.7 * self.SCALEFACTOR)  # sets the default seaborn chart colours and fonts
        coolcolour = "#daf8e3"

        self.device_list = TestPeripherals(parent = self)
        self.test_suite = TestSuite(name = f"OtO UNIT REFURBISHMENT {self.ProgramVersion}",
                            test_list=[
                                UnitInformation(name = "Information", parent = self),
                                TestExternalPower(name = "Charging", parent = self),
                                TestPump(name = "Pump 1", target_pump = 1, target_pump_duty = 100, parent = self),
                                TestPump(name = "Pump 2", target_pump = 2, target_pump_duty = 100, parent = self),
                                TestPump(name = "Pump 3", target_pump = 3, target_pump_duty = 100, parent = self),
                                NozzleHome(name = "Nozzle Home", parent = self),
                                PressureCheck(name = "Pressure Sensor", data_collection_time = 2.1, class_function= "EOL" , valve_target = None, parent = self),
                                ValveCalibration(name = "Valve Calibration", parent = self, reset = True),
                                ClosedLeakCheck(name = "Closed Leak Check", parent = self),
                                ConfirmValvePosition(name = "Confirm Valve Position", parent = self),
                                NozzleRotation(name = "Nozzle Rotation", parent = self),
                                CheckVacSwitch(name = "Vacuum Holds", parent = self),
                                TestSolar(name = "Solar", parent = self),
                                PrintDeviceLabel(name = "Print Labels", parent = self)
                                ],  
                            test_devices = self.device_list,
                            test_type = "EOL")
        
        self.csv_file_name:pathlib.Path = None
        self.log_file_directory: pathlib.Path = None

        # Fixed Window Elements
        self.status_font = font.Font(family = self.FONTFAMILY, size = int(28 * self.SCALEFACTOR), weight = "normal")
        self.smaller_font = font.Font(family = self.FONTFAMILY, size = int(26 * self.SCALEFACTOR), weight = "normal")
        style = ttk.Style(self)
        style.configure('TCheckbutton', font = self.status_font, background = coolcolour)
        self.winfo_toplevel().title(self.test_suite.name)

        self.LeftFrame = tk.Frame(self, width = int(1200 * self.SCALEFACTOR), height = int(2100 * self.SCALEFACTOR), relief = "sunken", border = int(5 * self.SCALEFACTOR), background = coolcolour)
        self.LeftFrame.grid(row = 0, column = 0, padx = int(5 *self.SCALEFACTOR), pady = int (5 * self.SCALEFACTOR))
        self.RightFrame = tk.Frame(self, width = int(2200 * self.SCALEFACTOR), height = int(2100 * self.SCALEFACTOR), relief = "raised", border = int(5 * self.SCALEFACTOR))
        self.RightFrame.grid(row = 0, column = 1, padx = int(5 *self.SCALEFACTOR), pady = int (5 * self.SCALEFACTOR))        
        self.text_console = tk.Text(self.RightFrame, relief = "raised", border = int(5 *self.SCALEFACTOR), font = self.smaller_font, padx = int(10 * self.SCALEFACTOR), pady = int(10 * self.SCALEFACTOR), height = 16)
        self.GraphHolder = tk.Frame(self.RightFrame, bg = self.NORMAL_COLOUR, relief = "sunken", border = int(5 *self.SCALEFACTOR), width = int(2000 * self.SCALEFACTOR), height = int(1300 * self.SCALEFACTOR))
        self.GraphHolder.grid_propagate(False)

        TextWidth = 17
        self.label_device_id = tk.Label(self.LeftFrame, text = "Unit Name:", font = self.smaller_font, padx = int(5 * self.SCALEFACTOR), background = coolcolour)
        self.text_device_id = tk.Label(self.LeftFrame, width = TextWidth, font = self.smaller_font, height = 1, padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR), borderwidth = int(5 * self.SCALEFACTOR), relief = "raised", anchor = "w")
        self.label_bom_number = tk.Label(self.LeftFrame, text = "BOM:", font = self.smaller_font, padx = int(5 * self.SCALEFACTOR), background = coolcolour)
        self.text_bom_number = tk.Label(self.LeftFrame, width = TextWidth, font = self.smaller_font, height = 1, padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR), borderwidth = int(5 * self.SCALEFACTOR), relief = "raised", anchor = "w")
        self.labelFirmware = tk.Label(self.LeftFrame, text = "Firmware:", font = self.smaller_font, padx = int(5 * self.SCALEFACTOR), background = coolcolour)
        self.textFirmware = tk.Label(self.LeftFrame, width = TextWidth, font = self.smaller_font, height = 1, padx = int(5 * self.SCALEFACTOR), pady = int (5 * self.SCALEFACTOR), borderwidth = int(5 * self.SCALEFACTOR), relief = "raised", anchor = "w")
        self.label_battery = tk.Label(self.LeftFrame, text = "Battery:", font = self.smaller_font, padx = int(5 * self.SCALEFACTOR), background = coolcolour)
        self.text_battery = tk.Label(self.LeftFrame, width = TextWidth, font = self.smaller_font, height = 1, padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR), borderwidth = int(5 * self.SCALEFACTOR), relief = "raised", anchor = "w")
        self.labelMAC = tk.Label(self.LeftFrame, text = "MAC:", font = self.smaller_font, padx = int(5 * self.SCALEFACTOR), background = coolcolour)
        self.textMAC = tk.Label(self.LeftFrame, width = TextWidth, font = self.smaller_font, height = 1, padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR), borderwidth = int(5 * self.SCALEFACTOR), relief = "raised", anchor = "w")
        self.CleanOnlyCheckBox = ttk.Checkbutton(self.LeftFrame, text = " CLEANED ONLY", command = self.CleanedOnlyChecked, variable = self.CleanOnly)
        self.ReplacePartsCheckBox = ttk.Checkbutton(self.LeftFrame, text = " REPLACE PARTS", command = self.ReplacePartsChecked, variable = self.ReplaceParts)

        # Program Variables
        self.abort_test_bool: bool = False
        self.test_result_list: List[TestResult] = []
        self.test_start_time: float = 0.0

        # User-Created Window Elements
        self.status_labels: List[tk.Label] = []
        self.buttons: List[tk.Button] = []
        self.all_elements = [self.status_labels, self.buttons]

        # Widgets: Buttons
        self.one_button_to_rule_them_all = tk.Button(self.LeftFrame, text = "START", width = 16, font = font.Font(family = self.FONTFAMILY, size = int(36 * self.SCALEFACTOR), weight = "bold"), pady = int(5 * self.SCALEFACTOR), bg = self.GOOD_COLOUR, fg = self.NORMAL_COLOUR, command = self.execute_tests)
        self.turn_valve_button = tk.Button(self.LeftFrame, text = "Turn Valve 90°", width = 16, font = font.Font(family = self.FONTFAMILY, size = int(36 * self.SCALEFACTOR), weight = "bold"), pady = int(5 * self.SCALEFACTOR), bg = self.GOOD_COLOUR, fg = self.NORMAL_COLOUR, command = self.TurnValve90)
        self.buttons.append(self.one_button_to_rule_them_all)
        self.buttons.append(self.turn_valve_button)

        # Grids for placement of elements
        self.text_console.grid(row = 0, column = 0, rowspan = 7, padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR), sticky = "NEWS")
        self.GraphHolder.grid(row = 7, column = 0, rowspan = 14, padx = int(5 * self.SCALEFACTOR), sticky = "NEWS")
        self.label_device_id.grid(row = 4, column = 0, sticky = "E", padx = int(10 * self.SCALEFACTOR))
        self.text_device_id.grid(row = 4, column = 1, padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR))
        self.label_bom_number.grid(row = 5, column = 0, sticky = "E", padx = int(10 * self.SCALEFACTOR))
        self.text_bom_number.grid(row = 5, column = 1, sticky = "W", padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR))
        self.labelFirmware.grid(row = 6, column = 0, sticky = "E", padx = int(10 * self.SCALEFACTOR))
        self.textFirmware.grid(row = 6, column = 1, sticky = "W", padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR))
        self.label_battery.grid(row = 7, column = 0, sticky = "E", padx = int(10 * self.SCALEFACTOR))
        self.text_battery.grid(row = 7, column = 1, sticky = "W", padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR))
        self.labelMAC.grid(row = 8, column = 0, sticky = "E", padx = int(10 * self.SCALEFACTOR))
        self.textMAC.grid(row = 8, column = 1, sticky = "W", padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR))
        self.one_button_to_rule_them_all.grid(row = 0, rowspan = 2, column = 0, columnspan = 2, padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR))
        self.turn_valve_button.grid(row = 13, column = 0, columnspan = 2, padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR))
        self.CleanOnlyCheckBox.grid(row = 2, column = 0, columnspan = 2)
        self.ReplacePartsCheckBox.grid(row = 3, column = 0, columnspan = 2)

        # Button Setup
        ColumnCount = 14  # number of items per column
        for count, steps in enumerate(self.test_suite.test_list):
            column_no = 3 + count // ColumnCount
            row_no = count % ColumnCount
            setattr(self, steps.name, tk.Button(self.LeftFrame, borderwidth = int(5 * self.SCALEFACTOR), relief = "raised", text = steps.name, bg = self.NORMAL_COLOUR, font = self.status_font, padx = int(5 * self.SCALEFACTOR), pady = int(5 * self.SCALEFACTOR), width = 24, wraplength = 490 * self.SCALEFACTOR, height = 2, command = lambda x=count : self.OneTestButton(x)))
            temp = getattr(self, steps.name)
            self.status_labels.append(temp)
            temp.grid(row = row_no, column = column_no, sticky = "EW", padx = int(10 * self.SCALEFACTOR), pady = int(6 * self.SCALEFACTOR))

    def abort_test(self):
        "Function to STOP test"
        self.one_button_to_rule_them_all["state"] = "disabled"
        self.abort_test_bool = True
        self.one_button_to_rule_them_all.update()

    def CleanedOnlyChecked(self):
        # make sure ReplacePartsCheckBox is not selected if CleanedOnly is.
        if self.CleanOnly.get() == 1:
            self.ReplaceParts.set(0)
    
    def ReplacePartsChecked(self):
        # make sure CleanOnlyCheckBox is not selected if ReplaceParts is.
        if self.ReplaceParts.get() == 1:
            self.CleanOnly.set(0)

    def clear_plot(self):
        "clears all items in the plot frame"
        for widgets in self.GraphHolder.winfo_children():
            widgets.destroy()

    def create_plot(self, window, plottype: str, xaxis, yaxis, size, name, clear, xtitle = None, ytitle = None):
        """creates a plot of type histogram, line, or polar in the plot frame"""
        self.clear_plot()
        plotit = False
        if plottype == "histplot":
            figure = plt.figure(0, figsize = (self.FIGSIZEX, self.FIGSIZEY), dpi = self.DPI)
            sns.histplot(data = xaxis)
            plt.title(name)
            plt.xlabel(xtitle)
            plotit = True
        elif plottype == "fohistplot":
            figure = plt.figure(2, figsize = (self.FIGSIZEX, self.FIGSIZEY), dpi = self.DPI)
            sns.histplot(data = xaxis)
            plt.title(name)
            plt.xlabel(xtitle)
            plotit = True
        elif plottype == "lineplot":
            figure = plt.figure(1, figsize = (self.FIGSIZEX, self.FIGSIZEY), dpi = self.DPI)
            if size > 10:
                sns.scatterplot(x = xaxis, y = yaxis, marker = "o", s = size)
            else:
                sns.lineplot(x = xaxis, y = yaxis)
            plt.title(name)
            plt.xlabel(xtitle)
            plt.ylabel(ytitle)
            plotit = True
        elif plottype == "polar":
            figure = plt.figure(3, figsize = (self.FIGSIZEX, self.FIGSIZEY), dpi = self.DPI)
            plt.polar(xaxis, yaxis, "r")
            plt.title(name)
            plotit = True
        if plotit:
            canvas = FigureCanvasTkAgg(figure, master = window)
            canvas.get_tk_widget().grid()
            self.GraphHolder.update()
            if clear:
                plt.close()

    def eol_pcb_init(self):
        """turns all EOL board pins off"""
        self.test_suite.test_devices.gpioSuite.ledPanelPin.set(1)
        self.test_suite.test_devices.gpioSuite.airSolenoidPin.set(1)
        self.test_suite.test_devices.gpioSuite.extPowerPin.set(1)
        self.test_suite.test_devices.gpioSuite.waterSolenoidPin.set(1)

    def establish_file_write_location(self):
        "sets and creates the directory for writing the main weekly data file for this station"
        is_testing = False  # set this to True to store data outside of the production folder
        if self.test_suite.test_devices.DUTsprinkler.logFileDirectory is None:
            self.test_suite.test_devices.DUTsprinkler.logFileDirectory = pathlib.Path("C:\Data")
            pathlib.Path(self.test_suite.test_devices.DUTsprinkler.logFileDirectory).mkdir(parents = True, exist_ok = True)
        self.log_file_directory = self.test_suite.test_devices.DUTsprinkler.logFileDirectory
        if is_testing == True:
            test_folder = "Test Folder"
            self.log_file_directory = (pathlib.Path(self.log_file_directory) /  test_folder)
            filename = "-TestProductionData" + str(time.strftime("%y", time.localtime())) + format(datetime.datetime.now().isocalendar()[1],"02d") + ".csv"
        else: 
            filename = "ReturnsData.csv"
        self.csv_file_name = (pathlib.Path(self.log_file_directory)/(str(self.test_suite.test_devices.DUTsprinkler.testFixtureName) + filename ))

    def execute_tests(self):
        "called when START button is pressed"
        if self.one_button_to_rule_them_all["state"] == "disabled" or self.turn_valve_button["state"] == "disabled":
            return None  # running another test, so don't start a new one
        else:
            self.turn_valve_button.configure(state = "disabled") # prevent button from working
            self.one_button_to_rule_them_all.configure(text = "STOP", bg = self.IN_PROCESS_COLOUR, fg = "BLACK", command = self.abort_test, state = "normal") 
            self.one_button_to_rule_them_all.update()

        # Step 1: Reinitialize Program Variables, make sure clean or replace toggle is set
        self.abort_test_bool: bool = False
        self.test_result_list: List[TestResult] = []
        self.test_start_time: float = 0.0
        if self.CleanOnly.get() == 0 and self.ReplaceParts.get() == 0:
            self.text_console.configure(bg = self.IN_PROCESS_COLOUR)
            self.one_button_to_rule_them_all.configure(text = "START", bg = self.GOOD_COLOUR, fg = self.NORMAL_COLOUR, command = self.execute_tests, state = "normal")
            self.turn_valve_button.configure(state = "normal")
            self.text_console_logger("Please select one of the CLEAN ONLY or REPLACE PARTS check boxes")
            return None

        # Step 2: Clean up window view, check for more than 1 USB board attached, start timer
        self.reset_status_color()
        if not self.USBCheck():
            self.text_console.configure(bg = self.IN_PROCESS_COLOUR)
            self.one_button_to_rule_them_all.configure(text = "START", bg = self.GOOD_COLOUR, fg = self.NORMAL_COLOUR, command = self.execute_tests, state = "normal")
            self.turn_valve_button.configure(state = "normal")
            return None
        self.test_start_time = timeit.default_timer()

        try:  # All encompassing error catch

            # Step 3: Restart device and reinitialize objects
            self.initialize_devices()
            if self.test_suite.test_type == "EOL": # reset all pin states
                self.eol_pcb_init()
                self.vac_interrupt()

            #Step 4: Run the test Suite
            index = 0
            self.test_suite.test_devices.DUTsprinkler.passEOL = True            
            while self.abort_test_bool is False and index < len(self.test_suite.test_list):
                self.status_labels[index].config(bg = self.IN_PROCESS_COLOUR)
                self.status_labels[index].update()
                self.test_result_list.append(self.test_suite.test_list[index].run_step(peripherals_list=self.test_suite.test_devices))
                if not self.test_result_list[index].is_passed:
                    self.test_suite.test_devices.DUTsprinkler.passEOL = False
                    self.test_step_failure_handler(step_number = index)
                    # self.test_suite.test_devices.DUTsprinkler.passTime = round((timeit.default_timer() - self.test_start_time), 4)
                    # self.log_unit_data()
                    # self.one_button_to_rule_them_all.configure(text = "START", bg = self.GOOD_COLOUR, fg = self.NORMAL_COLOUR, command = self.execute_tests, state = "normal")
                    # self.turn_valve_button.configure(state = "normal")
                    # return ClosePort(self.device_list)
                else:
                    self.status_labels[index].configure(bg = self.GOOD_COLOUR)
                    self.status_labels[index].update()
                    if self.test_result_list[index].test_status != None:
                        self.text_console_logger(display_message = self.test_result_list[index].test_status[1:])
                index += 1

            #Step 5: While Loop Complete or Escaped
            if self.abort_test_bool is True:
                self.text_console_logger(display_message="Stop button pressed, no results saved.")
                self.text_console_logger('----------------------- Test was STOPPED ----------------------------------')
                self.one_button_to_rule_them_all.configure(text = "START", bg = self.GOOD_COLOUR, fg = self.NORMAL_COLOUR, command = self.execute_tests, state = "normal")
                self.turn_valve_button.configure(state = "normal")
                return ClosePort(self.device_list)
            else:
                self.test_suite.test_devices.DUTsprinkler.passTime = round((timeit.default_timer() - self.test_start_time), 4)
                self.log_unit_data()
                if self.test_suite.test_devices.DUTsprinkler.passEOL:
                    self.text_console_logger("--------------------------  Device PASSED  -------------------------------")
                else:
                    self.text_console_logger("--------------------------  Device FAILED  -------------------------------")

            # Step 6: Reset Button Status
            self.one_button_to_rule_them_all.configure(text = "START", bg = self.GOOD_COLOUR, fg = self.NORMAL_COLOUR, command = self.execute_tests, state = "normal")
            self.turn_valve_button.configure(state = "normal")

        except Exception as e:
            if hasattr(self.test_suite.test_devices, "gpioSuite"):
                self.eol_pcb_init()  # Turns off power, air and LED
            self.text_console.configure(bg = self.IN_PROCESS_COLOUR)
            if str(e) == "Ping Failed":
                self.text_console_logger("No OtO found. Check that the grey ribbon cable is plugged into OtO.")
            elif str(e) == "No Otos found on Serial Ports":
                self.text_console_logger("No serial card found. Check that the USB communication serial card is plugged in.")
            else:
                self.text_console_logger(display_message = str(e))
            self.one_button_to_rule_them_all.configure(text = "START", bg = self.GOOD_COLOUR, fg = self.NORMAL_COLOUR, command = self.execute_tests, state = "normal")
            self.turn_valve_button.configure(state = "normal")

        return ClosePort(self.device_list)

    def initialize_devices(self):
        "Add otoSprinkler instance, establish gpio and i2c communications to the Cypress chip"

        try:
            if self.test_suite.test_type == "EOL":
                if not hasattr(self.test_suite.test_devices, "gpioSuite"):
                    new_gpio = GpioSuite()
                    self.test_suite.test_devices.add_device(new_object = new_gpio)
                if not hasattr(self.test_suite.test_devices,"i2cSuite"):
                    new_i2c = I2CSuite()
                    self.test_suite.test_devices.add_device(new_object = new_i2c)
                new_oto = otoSprinkler()
                self.test_suite.test_devices.add_device(new_object = new_oto)  # always reinitialize connection and create new sprinkler
                # pull info from the EOL PCB. factoryLocation and fixture name
                self.test_suite.test_devices.DUTsprinkler.factoryLocation, self.test_suite.test_devices.DUTsprinkler.testFixtureName = self.test_suite.test_devices.gpioSuite.getBoardInfo()
            else:
                self.text_console_logger(display_message = "UNEXPECTED PROGRAM ERROR!")
        except Exception as e:
            raise Exception(str(e))

    def log_unit_data(self):
        "logging raw data about the testSteps. every single testStep in the testSuite run must be added to this function otherwise it will error out"

        write_header: bool = True
        self.establish_file_write_location()
        log_file_columns = ["Entry Time", "Device ID", "MAC Address", "Firmware", "BOM", "Batch", "Unit Name Time", "Battery", "Battery Time", "Ext Power I","Ext Power V", "Ext Power Time",
                            "Pump 1 Time", "Pump 1 Ave Current", "Pump 1 Current STD", "Pump 2 Time", "Pump 2 Ave Current", "Pump 2 Current STD", "Pump 3 Time", "Pump 3 Ave Current", "Pump 3 Current STD",
                            "Nozzle Offset", "Nozzle Home Time","0 Pressure", "0 Pressure STD", "0 Pressure Time", "Valve Offset", "Valve Offset Time", "Valve Ave Current", "Valve Current STD",
                            "Peak 1 Pressure", "Peak 1 Angle", "Peak 2 Pressure", "Peak 2 Angle", "Closed Pressure", "Closed Pressure STD", "Closed Pressure Time", "Fully Open Trials",
                            "Fully Open 1 Ave", "Fully Open 1 STD", "Fully Open 3 Ave", "Fully Open 3 STD", "Fully Open Time", "Nozzle Speed", "Nozzle Speed STD", "Nozzle Time", "Nozzle Ave Current",
                            "Nozzle Current STD", "Vacuum Fail", "Vacuum Time", "Solar Voltage", "Solar Current", "Solar Time", "Cloud Save", "Cloud Time", "Printed", "Print Time", "Pass Time", "Passed"]

        if pathlib.Path(self.csv_file_name).exists():
            write_header = False
        else:
            pathlib.Path(self.log_file_directory).mkdir(parents = True, exist_ok = True)

        with open(self.csv_file_name, mode = "a", newline = "") as log_file:
            csv_writer = csv.DictWriter(log_file, fieldnames = log_file_columns)
            if write_header is True:
                csv_writer.writeheader()
            default_row = { "Entry Time": datetime.datetime.now(),
                            "Device ID": self.test_suite.test_devices.DUTsprinkler.deviceID,
                            "MAC Address": self.test_suite.test_devices.DUTsprinkler.macAddress,
                            "Firmware": self.test_suite.test_devices.DUTsprinkler.Firmware,
                            "BOM": self.test_suite.test_devices.DUTsprinkler.bomNumber,
                            "Batch": self.test_suite.test_devices.DUTsprinkler.batchNumber,
                            "Unit Name Time": None,
                            "Battery": None,
                            "Battery Time": None,
                            "Ext Power I": None,
                            "Ext Power V": None,
                            "Ext Power Time": None,
                            "Pump 1 Time": None,
                            "Pump 1 Ave Current": None,
                            "Pump 1 Current STD": None,
                            "Pump 2 Time": None,
                            "Pump 2 Ave Current": None,
                            "Pump 2 Current STD": None,
                            "Pump 3 Time": None,
                            "Pump 3 Ave Current": None,
                            "Pump 3 Current STD": None,
                            "Nozzle Offset": None,
                            "Nozzle Home Time": None,
                            "0 Pressure": None,
                            "0 Pressure STD": None,
                            "0 Pressure Time": None,
                            "Valve Offset": None,
                            "Valve Offset Time": None,
                            "Valve Ave Current": None,
                            "Valve Current STD": None,
                            "Peak 1 Pressure": None,
                            "Peak 1 Angle": None,
                            "Peak 2 Pressure": None,
                            "Peak 2 Angle": None,
                            "Closed Pressure": None,
                            "Closed Pressure STD": None,
                            "Closed Pressure Time": None,                            
                            "Fully Open Trials": None,
                            "Fully Open 1 Ave": None,
                            "Fully Open 1 STD": None,
                            "Fully Open 3 Ave": None,
                            "Fully Open 3 STD": None,
                            "Fully Open Time": None,
                            "Nozzle Speed": None,
                            "Nozzle Speed STD": None,
                            "Nozzle Time": None,
                            "Nozzle Ave Current": None,
                            "Nozzle Current STD": None,
                            "Vacuum Fail": None,
                            "Vacuum Time": None,
                            "Solar Voltage": None,
                            "Solar Current": None,
                            "Solar Time": None,
                            "Cloud Save": None,
                            "Cloud Time": None,
                            "Printed": None,
                            "Print Time": None,
                            "Pass Time": self.test_suite.test_devices.DUTsprinkler.passTime,
                            "Passed": self.test_suite.test_devices.DUTsprinkler.passEOL
                            }

            CurrentPump = 1
            for entry in self.test_result_list:
                if entry.cycle_time > 0:
                    if isinstance(entry, UnitInformationResult):
                        default_row["Unit Name Time"] = entry.cycle_time
                    elif isinstance(entry, TestBatteryResult):
                        default_row["Battery Time"] = entry.cycle_time
                        default_row["Battery"] = self.test_suite.test_devices.DUTsprinkler.batteryVoltage
                    elif isinstance(entry, TestExternalPowerResult):
                        default_row["Ext Power Time"] = entry.cycle_time
                        default_row["Ext Power I"] = self.test_suite.test_devices.DUTsprinkler.extPowerCurrent
                        default_row["Ext Power V"] = self.test_suite.test_devices.DUTsprinkler.extPowerVoltage
                    elif isinstance(entry, TestPumpResult):
                        if CurrentPump == 1:
                            default_row["Pump 1 Time"] = entry.cycle_time
                            default_row["Pump 1 Ave Current"] = self.test_suite.test_devices.DUTsprinkler.Pump1CurrentAve
                            default_row["Pump 1 Current STD"] = self.test_suite.test_devices.DUTsprinkler.Pump1CurrentSTD
                            CurrentPump += 1
                        elif CurrentPump == 2:
                            default_row["Pump 2 Time"] = entry.cycle_time
                            default_row["Pump 2 Ave Current"] = self.test_suite.test_devices.DUTsprinkler.Pump2CurrentAve
                            default_row["Pump 2 Current STD"] = self.test_suite.test_devices.DUTsprinkler.Pump2CurrentSTD
                            CurrentPump += 1
                        elif CurrentPump == 3:
                            default_row["Pump 3 Time"] = entry.cycle_time
                            default_row["Pump 3 Ave Current"] = self.test_suite.test_devices.DUTsprinkler.Pump3CurrentAve
                            default_row["Pump 3 Current STD"] = self.test_suite.test_devices.DUTsprinkler.Pump3CurrentSTD
                            CurrentPump += 1
                    elif isinstance(entry, NozzleHomeResult):
                        default_row["Nozzle Home Time"] = entry.cycle_time
                        default_row["Nozzle Offset"] = self.test_suite.test_devices.DUTsprinkler.nozzleOffset
                    elif isinstance(entry, PressureCheckResult):
                        default_row["0 Pressure Time"] = entry.cycle_time
                        default_row["0 Pressure"] = self.test_suite.test_devices.DUTsprinkler.ZeroPressureAve
                        default_row["0 Pressure STD"] = self.test_suite.test_devices.DUTsprinkler.ZeroPressureSTD
                    elif isinstance(entry, ValveCalibrationResult):
                        default_row["Valve Offset Time"] = entry.cycle_time
                        default_row["Valve Ave Current"] = self.test_suite.test_devices.DUTsprinkler.ValveCurrentAve
                        default_row["Valve Current STD"] = self.test_suite.test_devices.DUTsprinkler.ValveCurrentSTD
                        default_row["Valve Offset"] = self.test_suite.test_devices.DUTsprinkler.valveOffset
                        default_row["Peak 1 Pressure"] = self.test_suite.test_devices.DUTsprinkler.ValvePeak1
                        default_row["Peak 1 Angle"] = self.test_suite.test_devices.DUTsprinkler.Peak1Angle
                        default_row["Peak 2 Pressure"] = self.test_suite.test_devices.DUTsprinkler.ValvePeak2
                        default_row["Peak 2 Angle"] = self.test_suite.test_devices.DUTsprinkler.Peak2Angle
                    elif isinstance(entry, ClosedLeakCheckResult):
                        default_row["Closed Pressure Time"] = entry.cycle_time
                        if self.test_suite.test_devices.DUTsprinkler.valveClosesAve > 0:
                            default_row["Closed Pressure"] = self.test_suite.test_devices.DUTsprinkler.valveClosesAve
                            default_row["Closed Pressure STD"] = self.test_suite.test_devices.DUTsprinkler.valveClosesSTD
                    elif isinstance(entry, ConfirmValvePositionResult):
                        default_row["Fully Open Time"] = entry.cycle_time
                        if self.test_suite.test_devices.DUTsprinkler.valveFullyOpenTrials > 0:
                            default_row["Fully Open Trials"] = self.test_suite.test_devices.DUTsprinkler.valveFullyOpenTrials
                            default_row["Fully Open 1 Ave"] = self.test_suite.test_devices.DUTsprinkler.valveFullyOpen1Ave
                            default_row["Fully Open 1 STD"] = self.test_suite.test_devices.DUTsprinkler.valveFullyOpen1STD
                            default_row["Fully Open 3 Ave"] = self.test_suite.test_devices.DUTsprinkler.valveFullyOpen3Ave
                            default_row["Fully Open 3 STD"] = self.test_suite.test_devices.DUTsprinkler.valveFullyOpen3STD
                    elif isinstance(entry, NozzleRotationResult):
                        default_row["Nozzle Time"] = entry.cycle_time
                        default_row["Nozzle Ave Current"] = self.test_suite.test_devices.DUTsprinkler.NozzleCurrentAve
                        default_row["Nozzle Current STD"] = self.test_suite.test_devices.DUTsprinkler.NozzleCurrentSTD
                        if self.test_suite.test_devices.DUTsprinkler.nozzleRotationAve > 0:
                            default_row["Nozzle Speed"] = self.test_suite.test_devices.DUTsprinkler.nozzleRotationAve
                            default_row["Nozzle Speed STD"] = self.test_suite.test_devices.DUTsprinkler.nozzleRotationSTD
                    elif isinstance(entry, CheckVacSwitchResult):
                        default_row["Vacuum Time"] = entry.cycle_time
                        default_row["Vacuum Fail"] = self.test_suite.test_devices.DUTsprinkler.vacuumFail
                    elif isinstance(entry, TestSolarResult):
                        default_row["Solar Time"] = entry.cycle_time
                        default_row["Solar Voltage"] = self.test_suite.test_devices.DUTsprinkler.solarVoltage
                        default_row["Solar Current"] = self.test_suite.test_devices.DUTsprinkler.solarCurrent                    
                    else:
                        print (type(entry))
                        raise TypeError(f'Program error, unknown test specified: {entry}')
            csv_writer.writerow(default_row)
    
    def OneTestButton(self, ButtonNumber):
        "function for handling single button press for device debugging purposes"
        if self.one_button_to_rule_them_all["state"] == "disabled" or self.turn_valve_button["state"] == "disabled":
            return None  # running another test, so don't start a new one
        else:
            self.one_button_to_rule_them_all.configure(state = "disabled")
            self.turn_valve_button.configure(state = "disabled")
        self.reset_status_color()
        FunctionName = self.status_labels[ButtonNumber]['text']
        self.status_labels[ButtonNumber].configure(bg = self.IN_PROCESS_COLOUR, state = "disabled")
        self.status_labels[ButtonNumber].update()
        if not self.USBCheck():
            self.text_console.configure(bg = self.IN_PROCESS_COLOUR)
            self.status_labels[ButtonNumber].configure(bg = self.NORMAL_COLOUR, state = "normal")
            self.status_labels[ButtonNumber].update()
            self.one_button_to_rule_them_all.configure(state = "normal")
            self.turn_valve_button.configure(state = "normal")
            return None

        if FunctionName in "Vacuum Holds Print Labels":
            self.text_console_logger("This test cannot be run by itself.")
            self.status_labels[ButtonNumber].configure(bg = self.NORMAL_COLOUR, state = "normal")
            self.status_labels[ButtonNumber].update()
            self.one_button_to_rule_them_all.configure(state = "normal")
            self.turn_valve_button.configure(state = "normal")
            return None
        elif FunctionName in "Pressure Sensor Nozzle Home Nozzle Rotation":  # these functions don't need control board
            try:
                self.test_suite.test_devices.add_device(new_object = otoSprinkler())
            except Exception as e:
                self.text_console.configure(bg = self.IN_PROCESS_COLOUR)
                if str(e) == "Ping Failed":
                    self.text_console_logger("No OtO found. Check that the grey ribbon cable is plugged into OtO.")
                elif str(e) == "No Otos found on Serial Port":
                    self.text_console_logger("No serial card found. Check that the USB communication serial card is plugged in.")
                else:
                    self.text_console_logger(display_message = str(e))
                self.status_labels[ButtonNumber].configure(bg = self.BAD_COLOUR, state = "normal")
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal") 
                return ClosePort(self.device_list)
            ResultList = self.test_suite.test_list[ButtonNumber].run_step(peripherals_list=self.test_suite.test_devices)
            if not ResultList.is_passed:
                self.status_labels[ButtonNumber].configure(bg = self.BAD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                self.text_console.configure(bg = self.BAD_COLOUR)
                self.text_console_logger(display_message = ResultList.test_status)
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")
            else:
                self.status_labels[ButtonNumber].configure(bg = self.GOOD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                if ResultList.test_status != None:
                    self.text_console_logger(display_message = ResultList.test_status[1:])
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")  
            return ClosePort(self.device_list)             
        try:  # all other functions require an OtO, so try to connect to one first...
            if FunctionName in "Test Pump 1 Test Pump 2 Test Pump 3":
                self.vac_interrupt()
            self.initialize_devices()
            self.eol_pcb_init()
        except Exception as e:
            self.text_console.configure(bg = self.IN_PROCESS_COLOUR)
            if str(e) == "Ping Failed":
                self.text_console_logger("No OtO found. Check that the grey ribbon cable is plugged into OtO.")
            elif str(e) == "No Otos found on Serial Port":
                self.text_console_logger("No serial card found. Check that the USB communication serial card is plugged in.")
            else:
                if len(str(e)) > 0:
                    self.text_console_logger(display_message = str(e))
                else:
                    self.text_console_logger(display_message = "UNEXPECTED PROGRAM ERROR!")
            self.status_labels[ButtonNumber].configure(bg = self.BAD_COLOUR, state = "normal")
            self.one_button_to_rule_them_all.configure(state = "normal")
            self.turn_valve_button.configure(state = "normal")               
            return ClosePort(self.device_list)
        if FunctionName in "Test Pump 1 Test Pump 2 Test Pump 3":
            ResultList = self.test_suite.test_list[ButtonNumber].run_step(peripherals_list=self.test_suite.test_devices)
            if not ResultList.is_passed:
                self.status_labels[ButtonNumber].configure(bg = self.BAD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                self.text_console.configure(bg = self.BAD_COLOUR)
                self.text_console_logger(display_message = ResultList.test_status)
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")
            else:
                self.status_labels[ButtonNumber].configure(bg = self.GOOD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                if ResultList.test_status != None:
                    self.text_console_logger(display_message = ResultList.test_status[1:])
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")
        elif FunctionName in "Information": 
            ResultList = self.test_suite.test_list[ButtonNumber].run_step(peripherals_list=self.test_suite.test_devices)
            if not ResultList.is_passed:
                self.status_labels[ButtonNumber].configure(bg = self.BAD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                self.text_console.configure(bg = self.BAD_COLOUR)
                self.text_console_logger(display_message = ResultList.test_status)
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")
            else:
                self.status_labels[ButtonNumber].configure(bg = self.GOOD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                if ResultList.test_status != None:
                    self.text_console_logger(display_message = ResultList.test_status[1:])
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")  
            return ClosePort(self.device_list)                
        elif FunctionName in "Charging":
            ResultList = self.test_suite.test_list[ButtonNumber].run_step(peripherals_list=self.test_suite.test_devices)  # OtO Charging
            if not ResultList.is_passed:
                self.status_labels[ButtonNumber].configure(bg = self.BAD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                self.text_console.configure(bg = self.BAD_COLOUR)
                self.text_console_logger(display_message = ResultList.test_status)
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")
            else:
                self.status_labels[ButtonNumber].configure(bg = self.GOOD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                if ResultList.test_status != None:
                    self.text_console_logger(display_message = ResultList.test_status[1:])
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")                           
        elif FunctionName in "Valve Calibration":
            ResultList = ValveCalibration(name = "Valve Calibration", parent = self, reset = False).run_step(peripherals_list = self.test_suite.test_devices)  # Run valve calibration
            if not ResultList.is_passed:
                self.status_labels[ButtonNumber].configure(bg = self.BAD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                self.text_console.configure(bg = self.BAD_COLOUR)
                self.text_console_logger(display_message = ResultList.test_status)
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")
            else:
                self.status_labels[ButtonNumber].configure(bg = self.GOOD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                if ResultList.test_status != None:
                    self.text_console_logger(display_message = ResultList.test_status[1:])
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")                           
                if ResultList.test_status != None:
                    self.text_console_logger(display_message = ResultList.test_status[1:])
        elif FunctionName in "Solar Confirm Valve Position":  # must turn air on and off to run these commands
            ResultList = self.test_suite.test_list[ButtonNumber].run_step(peripherals_list=self.test_suite.test_devices)  # Run selected test
            if not ResultList.is_passed:
                self.status_labels[ButtonNumber].configure(bg = self.BAD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                self.text_console.configure(bg = self.BAD_COLOUR)
                self.text_console_logger(display_message = ResultList.test_status)
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")
            else:
                self.status_labels[ButtonNumber].configure(bg = self.GOOD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                if ResultList.test_status != None:
                    self.text_console_logger(display_message = ResultList.test_status[1:])
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")
        elif FunctionName in "Closed Leak Check":
            PauseTime = 17
            ResultList = PressureCheck(name = "Zero Pressure Check", data_collection_time = 2.1, class_function= "EOL" , valve_target = None, parent = self).run_step(peripherals_list = self.test_suite.test_devices)
            if ResultList.test_status != None:
                self.text_console_logger(display_message = ResultList.test_status[1:])
            self.text_console_logger(display_message = f"Waiting {PauseTime} seconds")
            time.sleep(PauseTime)
            ResultList = self.test_suite.test_list[ButtonNumber].run_step(peripherals_list=self.test_suite.test_devices)  # Verify Valve Closes
            if not ResultList.is_passed:
                self.status_labels[ButtonNumber].configure(bg = self.BAD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                self.text_console.configure(bg = self.BAD_COLOUR)
                self.text_console_logger(display_message = ResultList.test_status)
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")
            else:
                self.status_labels[ButtonNumber].configure(bg = self.GOOD_COLOUR, state = "normal")
                self.status_labels[ButtonNumber].update()
                if ResultList.test_status != None:
                    self.text_console_logger(display_message = ResultList.test_status[1:])
                self.one_button_to_rule_them_all.configure(state = "normal")
                self.turn_valve_button.configure(state = "normal")                           
        return ClosePort(self.device_list)
    
    def reset_status_color(self):
        "Resets all the status box colors to normal"
        for widgets in self.status_labels:
            widgets.configure(bg = self.NORMAL_COLOUR)
            widgets.update()
        self.text_console.configure(bg = self.NORMAL_COLOUR)
        self.text_console.update()
        self.text_device_id.configure(text = "")
        self.text_bom_number.configure(text = "")
        self.textFirmware.configure(text = "")
        self.text_battery.configure(text = "")
        self.textMAC.configure(text = "")
        self.text_device_id.update()

        self.clear_plot()
        ClearFigures()

    def test_step_failure_handler(self, step_number: int):
        "the index is required to help display the correct message and log the correct error. Updates the label to red in the gui, runs the cloud function to log the error in Firebase, resets all the gpio pins to the OFF state"

        error_message = self.test_result_list[step_number].test_status
        self.test_suite.test_devices.DUTsprinkler.errorStep = error_message
        self.test_suite.test_devices.DUTsprinkler.errorStepName = type(self.test_result_list[step_number]).__name__
        self.status_labels[step_number].configure(bg = self.BAD_COLOUR)
        self.status_labels[step_number].update()
        # self.text_console.configure(bg = self.BAD_COLOUR)
        self.text_console_logger(display_message = error_message)
        # self.eol_pcb_init()  # Turns off power, air and LED
        # self.text_console_logger('---------------------------------  DEVICE FAILED  -----------------------------------------')

    def text_console_logger(self, display_message: str):
        "function to put text into the console of the gui"
        self.text_console.insert(tk.END,display_message + "\n")
        self.text_console.see(tk.END)
        self.text_console.update()

    def TurnValve90(self):
        "Turns the valve 90 degrees. Open valve for the 15 psi air leak check"
        if self.one_button_to_rule_them_all["state"] == "disabled" or self.turn_valve_button["state"] == "disabled":
            return None
        else:
            self.one_button_to_rule_them_all.configure(state = "disabled")
            self.turn_valve_button.configure(state = "disabled")

        self.reset_status_color()
        self.turn_valve_button.configure(text = "Turning...", bg = self.IN_PROCESS_COLOUR, state = "disabled")
        self.one_button_to_rule_them_all.configure(state = "disabled")
        self.text_console.configure(bg = self.NORMAL_COLOUR)

        if not self.USBCheck():
            self.text_console.configure(bg = self.IN_PROCESS_COLOUR)
            self.one_button_to_rule_them_all.configure(state = "normal")
            self.turn_valve_button.configure(state = "normal")
            return None

        try:
            self.test_suite.test_devices.add_device(new_object = otoSprinkler())
        except Exception as e:
            self.text_console.configure(bg = self.IN_PROCESS_COLOUR)
            if str(e) == "Ping Failed":
                self.text_console_logger("No OtO found. Check that the grey ribbon cable is plugged into OtO.")
            elif str(e) == "No Otos found on Serial Port":
                self.text_console_logger("No serial card found. Check that the USB communication serial card is plugged in.")
            else:
                if len(str(e)) > 0:
                    self.text_console_logger(display_message = str(e))
                else:
                    self.text_console_logger(display_message = "UNEXPECTED PROGRAM ERROR!")
            self.one_button_to_rule_them_all.configure(state = "normal")
            self.turn_valve_button.configure(text = "Turn Valve 90°", bg = self.GOOD_COLOUR, command = self.TurnValve90, state = "normal") 
            return ClosePort(self.device_list)

        self.text_console_logger("Turning ball valve 90°...")
        try:
            currentPosition = int(self.test_suite.test_devices.DUTMLB.get_sensors().valve_position_centideg)
            desiredPosition = (currentPosition + 9000) % 36000
            ReturnMessage = self.test_suite.test_devices.DUTMLB.set_valve_position(valve_position_centideg = desiredPosition, wait_for_complete = True)
            if ReturnMessage.message_type_string != "CTRL_OUT_COMMAND_COMPLETE":
                self.text_console.configure(bg = self.BAD_COLOUR)
                self.text_console_logger("Valve turn was NOT successful.")
                self.turn_valve_button.configure(text = "Turn Valve 90°", bg = self.GOOD_COLOUR, command = self.TurnValve90, state = "normal")
                self.one_button_to_rule_them_all.configure(state = "normal")            
                return ClosePort(self.device_list)
        except Exception as e:
            self.text_console.configure(bg = self.BAD_COLOUR)
            self.text_console_logger("Valve turn was NOT successful.")
            self.turn_valve_button.configure(text = "Turn Valve 90°", bg = self.GOOD_COLOUR, command = self.TurnValve90, state = "normal")
            self.one_button_to_rule_them_all.configure(state = "normal")
            return ClosePort(self.device_list)
        self.text_console_logger(display_message = "Valve successfully turned.")
        self.turn_valve_button.configure(text = "Turn Valve 90°", bg = self.GOOD_COLOUR, command = self.TurnValve90, state = "normal")
        self.one_button_to_rule_them_all.configure(state = "normal")
        return ClosePort(self.device_list)

    def USBCheck(self):
        "Confirm only one OtO serial card is connected"
        USB_VID = 0x10C4
        USB_PID = 0xEA60
        PortList = serial.tools.list_ports.comports()
        OtOPortList = []
        for port in PortList:
            if port.pid == USB_PID and port.vid == USB_VID:
                OtOPortList.append(port.name)
        if len(OtOPortList) == 1:
            globalvars.PortName = OtOPortList[0]
            return True
        elif len(OtOPortList) > 1:
            self.text_console_logger("Too many USB cards attached for this test!")
        else:
            self.text_console_logger("No USB card found!")
        return False

    def vac_interrupt(self):
        "checks vacuum switches are not triggered prior to testing"
        if not hasattr(self.test_suite.test_devices,"gpioSuite"):
            try:
                new_gpio = GpioSuite()
                self.test_suite.test_devices.add_device(new_object = new_gpio)
            except:
                raise VacError("TEST CONTROLLER WASN'T FOUND. Is it plugged in?")
        if self.test_suite.test_devices.gpioSuite.vacSwitchPin1.get() == 0 or self.test_suite.test_devices.gpioSuite.vacSwitchPin2.get() == 0 or self.test_suite.test_devices.gpioSuite.vacSwitchPin3.get() == 0:
            raise VacError("Unscrew and then retighten the black, blue and orange caps before testing again.")

def ClearFigures():
    "clears all graphs and the memory associated with them"
    plt.figure(0)
    plt.close()
    plt.figure(1)
    plt.close()
    plt.figure(2)
    plt.close()
    plt.figure(3)
    plt.close()

def ClosePort(DeviceList: TestPeripherals):
    "Closes the USB port if it is open and connected to an OtO"
    if hasattr(DeviceList, "DUTMLB"):
        if hasattr(DeviceList.DUTMLB, "connection"):
            if hasattr(DeviceList.DUTMLB.connection, "port"):
                return DeviceList.DUTMLB.stop_connection()
    return None

if __name__ == '__main__':
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # gets rid of the fuzzies on graphics display
    Application = MainWindow()
    Application.state('zoomed')
    Application.grid()
    Application.mainloop()
    ClearFigures()
    exit()