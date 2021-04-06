import asyncio,threading
from time import sleep
from bleak import discover,BleakClient
# Port de https://github.com/madhead/saberlight/blob/master/protocols/Triones/protocol.md
class ledBle:

    address = "ff:ff:95:01:c2:17"
    chc = "0000ffd9-0000-1000-8000-00805f9b34fb"
    loop = asyncio.get_event_loop()
    
    async def con(self, address, loop):
        self.client = BleakClient(self.address, loop=loop)
        try:
            await self.client.connect()
            #print("Conectado")
        except Exception as e:
            print(e)
            return
        finally:
            srvs = await self.client.get_services()
            return self.client
            #await app.run(host='0.0.0.0', port=3100, debug=True)
            #await self.client.write_gatt_char(chc, ledoff)
            #await self.client.disconnect()

    async def senddata(self, miobj, data):
        self.client = miobj
        #print(await self.client.is_connected() )
        await self.client.write_gatt_char(self.chc, data)

    async def discn(self, miobj):
        self.client = miobj
        await self.client.disconnect()
        #print('Desconectado.')
    
    def connect_ble(self):
        #print("Conecta")
        global miobj
        miobj = self.loop.run_until_complete(self.con(self.address, self.loop))
        
    def set_state(self,estado):
        if estado == 'on':
            valor =bytearray(b"\xcc\x23\x33")
        else:
            valor =bytearray(b"\xcc\x24\x33")
        #print(valor)
        self.loop.run_until_complete(self.senddata(miobj, valor))
        return "ok"

    def set_color(self, micolor):
        red = bytearray.fromhex(micolor[1:3])
        green = bytearray.fromhex(micolor[3:5])
        blue = bytearray.fromhex(micolor[5:7])
        valor = bytearray(b"\x56" + red + green + blue + b"\x00\xf0\xaa")
        #print(valor)
        self.loop.run_until_complete(self.senddata(miobj, valor))
        return "ok"

    def set_effect(self, efecto,speed):
        effect = bytearray.fromhex(efecto)
        speed = bytearray.fromhex(speed)
        valor = bytearray(b"\xbb" + effect + speed + b"\x44")
        #print(efecto, speed)
        self.loop.run_until_complete(self.senddata(miobj, valor))
        return "ok"

    def set_white(self):
        valor = bytearray(b"\x56\x00\x00\x00\xff\x0f\xaa")
        self.loop.run_until_complete(self.senddata(miobj, valor))
        return "ok"

    def disconnect_ble(self):
        self.loop.run_until_complete(self.discn(miobj))

def runleds():
    ledConnector = ledBle()
    ledConnector.connect_ble()
    ledConnector.set_state('on')
    ledConnector.set_color('#ff0000')
    sleep(2)
    ledConnector.set_color('#00ff00')
    sleep(2)
    ledConnector.set_color('#0000ff')
    sleep(2)
    ledConnector.set_state('off')
    ledConnector.disconnect_ble()

def loop_uf():
    for i in range(30):
        sleep(.5)
        print(i)

if __name__ == "__main__":
    #threading.Thread(target=loop_uf).start()
    runleds()
#print("envia dato")
#loop.run_until_complete(senddata(miobj, ledon))
#print("desconecta")
