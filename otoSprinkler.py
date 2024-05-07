import pathlib
import time

class otoSprinkler:
    '''
    Represents attributes of a generic oto sprinkler. All these value will either be written to the database or is required
    to describe a unique instance of this device.
    '''
    def __init__(self):
        self.deviceID: str = ""  # OtO serial number, format "oto1234567"
        self.macAddress: str = ""  # MAC address of the wifi of the ESP32
        self.UID: str = ""  # UID of unit
        self.SSID: str = ""  # SSID of wifi
        self.bomNumber: str = ""  # BOM number of OtO design, set manually at flash time, examples: 6014-G, 6014-F1
        self.Firmware: str = ""  # firmware revision of OtO board
        self.batchNumber = str(time.strftime("%y", time.localtime())[1] + time.strftime("%j", time.localtime()))  # format is YDDD, where Y is last digit of the year, and DDD is the day of the year of the current day

        self.batteryVoltage: float = 0

        self.extPowerCurrent: float = 0
        self.extPowerVoltage: float = 0

        self.nozzleOffset: int = 0  # represents actual ADC number of nozzle pointed straight ahead

        self.ZeroPressureAve: float = 0
        self.ZeroPressureSTD: float = 0

        self.valveOffset: int = 0  # represents actual ADC number of closed valve
        self.ValvePeak1: int = 0  # highest peak pressure ADC value
        self.Peak1Angle: int = 0  # absolute peak 1 angle value °
        self.ValvePeak2: int = 0  # 2nd highest peak pressure ADC value
        self.Peak2Angle: int = 0  # absolute peak 2 angle value °
        self.ValveCurrentAve: float = 0
        self.ValveCurrentSTD: float = 0

        self.valveClosesAve: float = 0
        self.valveClosesSTD: float = 0

        self.valveFullyOpen: int = 0
        self.valveFullyOpenTrials: int = 0
        self.valveFullyOpen1Ave: float = 0
        self.valveFullyOpen2Ave: float = 0
        self.valveFullyOpen3Ave: float = 0
        self.valveFullyOpen1STD: float = 0
        self.valveFullyOpen2STD: float = 0
        self.valveFullyOpen3STD: float = 0

        self.nozzleRotationAve: float = 0
        self.nozzleRotationSTD: float = 0
        self.NozzleCurrentAve: float = 0
        self.NozzleCurrentSTD: float = 0

        self.vacuumFail: int = 0   # 0 means all passed, binary 111 for failure (ie pump 1 and 2 = 3 decimal, 011 binary)

        self.solarVoltage: float = 0
        self.solarCurrent: float = 0

        self.CloudSave: bool = False

        self.Printed: bool = False
        self.PrintTime: float = 0

        self.Purged: bool = False
        self.PurgeTime: float = 0

        self.errorStep: str = ""  # this is a misnomer, it will contain the error MESSAGE from the failing test step
        self.valveRawData: list = []
        self.nozzleRotationData: list = []
        self.pump1Pass: bool = False
        self.Pump1CurrentAve: float = 0
        self.Pump1CurrentSTD: float = 0
        self.pump2Pass: bool = False
        self.Pump2CurrentAve: float = 0
        self.Pump2CurrentSTD: float = 0
        self.pump3Pass: bool = False
        self.Pump3CurrentAve: float = 0
        self.Pump3CurrentSTD: float = 0
        self.passEOL: bool = False
        self.passTime: float = 0
        self.bringUpComment = ""
        self.ZeroPressure: list = []
        self.ZeroPressure_Temp: list = []
        self.errorStepName: str = ""  # this is the name of the test result where we failed.
        self.factoryLocation: str = ""  # i.e. OTO_MFG or MEC0_MFG
        self.testFixtureName: str = ""  # i.e."OTO_EOL_1"
        self.logFileDirectory: pathlib.Path = None  # i.e. "C:\Users\JeffreyLaw\OneDrive - oto Lawn\Shared Documents\Production\Production Data\OTO\OTO_EOL_1"
        self.flagFirstTestRecording_counter: int = 0
        self.firstDateTime: str = ""
        self.testRunCounter: dict = {}
        self.fullyopenbuffer: int = 0
        self.FO_overall_test_counter: int = 1
        self.SubscribeFrequency: int = 0
        self.SlowerSubscribeFrequency: int = 0
        self.SubscribeOff: int = 0
        self.NoNVSException = None
        self.psig15: int = 0
        self.psig30: int = 0

