class OpfuncDevice:
    def __init__(self, DeviceID):
        self.DeviceID = DeviceID

    def open(self):
        pass

    def close(self):
        pass

    def reset(self):
        pass

    def write(self):
        pass

    def read(self):
        pass

    def getDeviceID(self):
        return self.DeviceID
        # pass


class OpfuncRF(OpfuncDevice):
    def __init__(self, DeviceID):
        super().__init__(DeviceID)

    def open(self):
        super().open()

    def close(self):
        super().close()

    def reset(self):
        super().reset()

    def read(self):
        super().read()

    def write(self):
        # return super().write()
        pass

    def getDeviceID(self):
        # print("RF Device ID: ", super().getDeviceID())
        pass

