import clr #package pythonnet, not clr
import sys
from time import sleep
from lib.getserial import listEBBports,serial
from infi.systray import SysTrayIcon
from subprocess import Popen
from typing import Optional
from ctypes import wintypes, windll, create_unicode_buffer, c_ulong,byref
from lib.ledble import ledBle
import json
import psutil
import os

def donothing(systray):
    pass


debug = False
openhardwaremonitor_hwtypes = ['Mainboard','SuperIO','CPU','RAM','GpuNvidia','GpuAti','TBalancer','Heatmaster','HDD']
openhardwaremonitor_sensortypes = ['Voltage','Clock','Temperature','Load','Fan','Flow','Control','Level','Factor','Power','Data','SmallData']

def connect_arduino():
    a_ports = list(listEBBports())
    if a_ports:
        comport = a_ports[0][0]
        ser = serial.Serial(comport, baudrate=9600,parity=serial.PARITY_NONE)
        #ser.setDTR(True)~~
        try:
            if(ser.is_open):
                ser.close()
            
            ser.open()
            sleep(1)
            return ser
        except:
            print("Error puerto!")

def getExeName() -> Optional[str]:
    hWnd = windll.user32.GetForegroundWindow()
    pid = c_ulong()
    result = windll.user32.GetWindowThreadProcessId(hWnd, byref(pid))
    return psutil.Process(pid.value).name()

colorjson = os.getenv('appdata') + '\\dlprofiler\\appcolors.json'
with open(colorjson) as jsondata:
    list_progs = json.load(jsondata)
def_color = (list(filter(lambda x:x['titulo']=='Default',list_progs['apps'])))[0]["color"]
def getColorApp(app_exe):
    ret_color = (list(filter(lambda x:app_exe in x['path'],list_progs['apps'])))
    if(ret_color):
        return ret_color[0]['color']
    else:
        return def_color

def initialize_openhardwaremonitor():
    file = r'OpenHardwareMonitorLib'
    clr.AddReference(file)

    from OpenHardwareMonitor import Hardware

    handle = Hardware.Computer()
    handle.MainboardEnabled = True
    handle.CPUEnabled = True
    handle.RAMEnabled = True
    handle.GPUEnabled = True
    handle.HDDEnabled = True
    handle.Open()
    return handle

def fetch_stats(handle):
    clocks =[]
    cputemp = 0
    cpuclock = 0
    cpuload = 0
    memused = 0
    gputemp = 0
    gpuload = 0
    gpuclock = 0
    for i in handle.Hardware:
        i.Update()
        for sensor in i.Sensors:
            r_values = parse_sensor(sensor)
            if r_values:
                r_type,r_value = (r_values[0], r_values[1])
                if(r_type=="cputemp"):
                    cputemp = r_value
                elif(r_type=="cpuclock"):
                    #cpuclock = r_value
                    clocks.append(int(r_value))
                elif(r_type=="cpuload"):
                    cpuload = r_value
                elif(r_type=="memused"):
                    memused = r_value
                elif(r_type=="gputemp"):
                    gputemp = r_value
                elif(r_type=="gpuload"):
                    gpuload = r_value
                elif(r_type=="gpuclock"):
                    gpuclock = r_value

        for j in i.SubHardware:
            j.Update()
            for subsensor in j.Sensors:
                r_values = parse_sensor(subsensor)
                if r_values:
                    r_type,r_value = (r_values[0], r_values[1])
                    if(r_type=="cputemp"):
                        cputemp = r_value
                    elif(r_type=="cpuclock"):
                        #cpuclock = r_value
                        clocks.append(int(r_value))
                    elif(r_type=="cpuload"):
                        cpuload = r_value
                    elif(r_type=="memused"):
                        memused = r_value
                    elif(r_type=="gputemp"):
                        gputemp = r_value
                    elif(r_type=="gpuload"):
                        gpuload = r_value
                    elif(r_type=="gpuclock"):
                        gpuclock = r_value
    if (len(clocks)>1):
        cpuclock = int(sum(clocks) / len(clocks))
            
    return (cputemp,cpuclock,cpuload,memused,gputemp,gpuload,gpuclock)

def parse_sensor(sensor):
        if sensor.Value is not None:
            
            sensortypes = openhardwaremonitor_sensortypes
            hardwaretypes = openhardwaremonitor_hwtypes
            origin = ""
            value = "0"
            if sensor.SensorType == sensortypes.index('Temperature') and \
            sensor.Hardware.HardwareType == hardwaretypes.index('CPU') and \
                u'package' in sensor.Name.lower():
                origin = 'cputemp'
                value = "%i" % (sensor.Value)

            elif sensor.SensorType == sensortypes.index('Load') and \
            sensor.Hardware.HardwareType == hardwaretypes.index('CPU') and \
                u'total' in sensor.Name.lower():
                origin = 'cpuload'
                value = "%i" % (sensor.Value)

            elif sensor.SensorType == sensortypes.index('Clock') and \
                sensor.Hardware.HardwareType == hardwaretypes.index('CPU') and\
                    u'bus'not in sensor.Name.lower():
                origin = 'cpuclock'
                value = "%i" % (sensor.Value)
            elif sensor.SensorType == sensortypes.index('Data') and \
                sensor.Hardware.HardwareType == hardwaretypes.index('RAM') and\
                u'used' in sensor.Name.lower():
                origin = 'memused'
                value = "{:0.2f}".format(sensor.Value)
            elif sensor.SensorType == sensortypes.index('Temperature') and \
                sensor.Hardware.HardwareType == hardwaretypes.index('GpuNvidia'):
                #print(f'HT: {sensor.Hardware.HardwareType} name: {sensor.Name} valor: {sensor.Value}')
                origin = 'gputemp'
                value = "%i" % (sensor.Value)
            elif sensor.SensorType == sensortypes.index('Load') and \
                sensor.Hardware.HardwareType == hardwaretypes.index('GpuNvidia') and\
                u'core' in sensor.Name.lower():
                origin = 'gpuload'
                value = "%i" % sensor.Value
            elif sensor.SensorType == sensortypes.index('Clock') and \
                sensor.Hardware.HardwareType == hardwaretypes.index('GpuNvidia') and\
                u'core' in sensor.Name.lower():
                origin = 'gpuclock'
                value = "%i" % sensor.Value                
                #print(f'HT: {sensor.Hardware.HardwareType} name: {sensor.Name} valor: {sensor.Value}')
            return (origin, value)

            

def update_arduino(hwhandle, ser_arduino):
    cputemp,cpuclock,cpuload,memused,gputemp,gpuload, gpuclock = (fetch_stats(hwhandle))
    out_buffer = bytearray(f"C{cputemp}c {cpuload}%|R{memused}G|GT:{gputemp}" \
                f"|KC:{gpuload}|GC:{gpuclock}|CHC{cpuclock}|","ANSI")
    #arduino.writelines(out_buffer)
    arduino.write(out_buffer)
    if(debug):
        print("envió " +   out_buffer.decode('ANSI') )

if __name__ == "__main__":
    if(len(sys.argv)>1):
        if (sys.argv[1]=='--debug'):
            print('modo debug ON')
            debug =True
    #listEBBports()
    #print("Ejecutando...")
    HardwareHandle = initialize_openhardwaremonitor()
    #fetch_stats(HardwareHandle)
    arduino=connect_arduino()
    ejecutar = True

    def Salir(sysTrayIcon):
        global ejecutar
        ejecutar = False

    def reiniciarLed(systray):
        # posh = [
        #     'powershell.exe',
        #     R'$callback=(ssh 192.168.1.222 . \Users\marcp\Desktop\Servled.ps1)'
        # ]
        # proc = Popen(posh, shell=True,
        #     stdin=None, stdout=None, stderr=None, close_fds=True)
        # print('reinciar')
        ledble.connect_ble()

    def apagarLed(systray):
        """ posh = [
            'powershell.exe',
            R'$callback=(wget -Uri "192.168.1.222:3100/switch/off")'
        ]
        proc = Popen(posh, shell=True,
            stdin=None, stdout=None, stderr=None, close_fds=True)
        print('apagar') """
        ledble.set_state('off')
        global mon_apps
        mon_apps = False

    def encenderLed(systray):
        """ posh = [
            'powershell.exe',
            R'$callback=(wget -Uri "192.168.1.222:3100/switch/on")'
        ]
        proc = Popen(posh, shell=True,
            stdin=None, stdout=None, stderr=None, close_fds=True)
        print('encender') """
        global mon_apps
        mon_apps=True
        ledble.set_state('on')

    hover_text = 'MCO-CPU Display'
    
        
    menu_items = (
        (f'Conectado a ({arduino.name})',None,donothing),
        #('Dispositivos bluetooth',None,donothing)
        ('Dispositivos Bluetooth',None,(('Ninguno', None,donothing),)),
        ('LED Escritorio', None, (
            ('Reinciar servicio',None,reiniciarLed),
            ('Encender LED Escritorio',None,encenderLed),
            ('Apagar LED Escritorio',None,apagarLed),
        )),
    )

    systray = SysTrayIcon("pyhw.ico", hover_text, menu_items, on_quit=Salir, default_menu_index=1)
    systray.QUIT='Salir'
    systray.start()
    ledble = ledBle()
    ledble.connect_ble()
    encenderLed(systray)

    if(arduino):
            while(ejecutar):
                if(mon_apps):
                    act_exe = getExeName()                
                    send_color = getColorApp(act_exe)
                    ledble.set_color(send_color)
                update_arduino(HardwareHandle,arduino)
                sleep(2)
            arduino.close()
            
    ledble.set_state('off')
    ledble.disconnect_ble()
    systray.shutdown()
