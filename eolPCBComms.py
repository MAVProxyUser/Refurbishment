from pyoto.cypressTest.ucdev.cy7c65211 import CyUSBSerial, CyGPIO, CyI2C
import pathlib
from pyoto.cypressTest.ltc2945 import LTC2945

#########
class GpioPin:
    def __init__(self, pinNumber: int, targetController):
        self.pinNumber: int = pinNumber
        self.controller: CyGPIO = targetController

    def get(self):
        try:
            return self.controller.get(self.pinNumber)
        except:
            return Exception

    def set(self, targetState: int):
        try:
            return self.controller.set(self.pinNumber, targetState) # will return nothing
        except:
            return Exception

class GpioSuite:
    GPIO_AIR_SOLENOID = 0
    GPIO_WATER_SOLENOID = 1
    GPIO_VAC_SWITCH_1 = 9
    GPIO_VAC_SWITCH_2 = 10
    GPIO_VAC_SWITCH_3 = 11
    GPIO_LED_PANEL = 2
    GPIO_12V_REGULATOR = 7

    def __init__(self):
        '''
        eventually this init should have the specific correct one passed in, right now it assumes there's only one controller
        and we take that one

        to call this,
        import this module, create a class i.e. gpioList = GpioSuite()
        gpioList.airSolenoidPin.get()
        gpioList.airSolenoidPin.set(targetState = 1 or 0)
        '''
        self.lib = CyUSBSerial(lib=str(pathlib.Path(__file__).parent/"pyoto"/"cypressTest"/"cyusbserial.dll"))
        try:
            self.gpioDev = list(self.lib.find(serialBlock=1))[0]
        except IndexError:
            raise Exception("TEST CONTROLLER WASN'T FOUND. Is it plugged in?")
        self.gpioController = CyGPIO(self.gpioDev)
        self.airSolenoidPin = GpioPin(pinNumber=self.GPIO_AIR_SOLENOID, targetController=self.gpioController)
        self.waterSolenoidPin = GpioPin(pinNumber=self.GPIO_WATER_SOLENOID, targetController=self.gpioController)
        self.vacSwitchPin1 = GpioPin(pinNumber=self.GPIO_VAC_SWITCH_1, targetController=self.gpioController)
        self.vacSwitchPin2 = GpioPin(pinNumber=self.GPIO_VAC_SWITCH_2, targetController=self.gpioController)
        self.vacSwitchPin3 = GpioPin(pinNumber=self.GPIO_VAC_SWITCH_3, targetController=self.gpioController)
        self.ledPanelPin = GpioPin(pinNumber=self.GPIO_LED_PANEL, targetController=self.gpioController)
        self.extPowerPin = GpioPin(pinNumber=self.GPIO_12V_REGULATOR, targetController=self.gpioController)

    def getBoardInfo(self):
        return self.lib.sendBoardInfo()

class I2CSuite:
    def __init__(self):
        self.lib = CyUSBSerial(lib=str(pathlib.Path(__file__).parent/"pyoto"/"cypressTest"/"cyusbserial.dll"))
        try:
            self.i2cDev = list(self.lib.find(serialBlock=0))[0]
        except IndexError:
            raise Exception("TEST CONTROLLER WASN'T FOUND. Is it plugged in?\n测试控制器没有找到, 是否已插入?")
        self.i2cController = CyI2C(self.i2cDev)
        self.i2cLTC2945 = LTC2945(self.i2cController)

#######################################################################################################################

