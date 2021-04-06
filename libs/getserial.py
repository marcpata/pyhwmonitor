import serial

def listEBBports():
    # Find and return a list of all EiBotBoard units
    # connected via USB port.
    try:
        from serial.tools.list_ports import comports
    except ImportError:
        return None
    if comports:
        com_ports_list = list(comports())
        ebb_ports_list = []
        for port in com_ports_list:
            port_has_ebb = False
            if port[1].startswith("USB Serial Port"):
                port_has_ebb = True
            elif port[2].startswith("USB VID:PID=0403:6001"):
                port_has_ebb = True
            if port_has_ebb:
                ebb_ports_list.append((port.name,port.description))
        if ebb_ports_list:
            return ebb_ports_list 

if __name__=='__main__':
    print ("Found ports:")
    for n,s in listEBBports():
        print ("(%s) %s" % (n,s))