import pyvisa
import time


#  read data type cast
def read_data_cast(func, res):
    if res["status"] == "pass":
        try:
            res["data"] = func(res["data"])
            return res
        except:
            return {"status": "fail"}
    else:
        return res
    
def transfer_1(val):
    transfer_dict = {1: 'On', 0: 'Off'}
    return transfer_dict[val]


class E8663D():
    """
    This class is used to control the angilent signal generator E8663D
    """
    
    def __init__(self, ip, power_limit=3):
        self.__rm = pyvisa.ResourceManager('@py')
        # print(self.__rm.list_resources("TCPIP?*"))
        self.__ip = ip
        self.__timeout = 0.05
        self.__power_limit = power_limit #unit dBm
        
        self.__get_socket = self.__rm.open_resource('TCPIP::' + self.__ip + '::inst0::INSTR')
        self.__set_socket = self.__rm.open_resource('TCPIP::' + self.__ip + '::inst0::INSTR')
        self.__get_socket.timeout = self.__timeout
        self.__set_socket.timeout = self.__timeout

        
    def close(self):
        """Close the socket connection to the instrument."""
        self.__get_socket.close()
        self.__set_socket.close()

    def reconnect(self):
        self.close()
        try:
            self.__get_socket = self.__rm.open_resource('TCPIP::' + self.__ip + '::inst0::INSTR')
            self.__set_socket = self.__rm.open_resource('TCPIP::' + self.__ip + '::inst0::INSTR')
            self.__get_socket.timeout = self.__timeout
            self.__set_socket.timeout = self.__timeout
        except:
            pass
        
    def __query(self, text):
        """Return the output of the query on text"""
        try:
            res = self.__get_socket.query(text)
            return {'status': 'pass', 'data': res}
        except:
            return {'status': 'conn_err'}

    def __write(self, text):
        """Sends a command to the instrument."""
        try:
            self.__set_socket.write(text)
            time.sleep(self.__timeout)
            return {'status': 'pass'}
        except:
            return {'status': 'conn_err'}
        
    def get_power(self):
        # 'On' / 'Off'
        return read_data_cast(transfer_1, read_data_cast(int, self.__query(':OUTPUT:STATE?')))

    def get_frequency(self):
        # unit is Hz
        return read_data_cast(float, self.__query(':SOURCE:FREQUENCY:CW?'))

    def get_level(self):
        # unit is dBm
        return read_data_cast(float, self.__query(':SOURCE:POWER:LEVEL:IMMEDIATE:AMPLITUDE?'))

    def set_power(self, state):
        if state == 'On':
            return self.__write(':OUTPUT:STATE ON')
        elif state == 'Off':
            return self.__write(':OUTPUT:STATE OFF')
        else:
            return {'status': 'fail'}

    def set_frequency(self, freq, unit='GHZ'):
        """set the frequency value"""
        return self.__write(':SOURCE:FREQUENCY:CW ' + str(freq) + unit)

    def set_level(self, level, unit='DBM'):
        """set the amplitude value"""
        if level > self.__power_limit:
            print("Level is over safe range!")
        else:
            return self.__write(':SOURCE:POWER:LEVEL:IMMEDIATE:AMPLITUDE ' + str(level) + unit)
    

if __name__ == "__main__":
    PSG = E8663D("192.168.1.15")
    freq = PSG.get_frequency()
    # res = PSG.set_level(1.4, unit='DBM')
    level = PSG.get_level()
    print(freq)
    print(level)