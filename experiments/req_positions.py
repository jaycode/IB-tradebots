"""
https://interactivebrokers.github.io/tws-api/positions.html
"""
from ibapi.wrapper import EWrapper, Contract
from ibapi.client import EClient
from threading import Thread
import queue

class TestWrapper(EWrapper):
    ## error handling code
    def init_error(self):
        error_queue=queue.Queue()
        self._my_errors = error_queue

    def get_error(self, timeout=5):
        if self.is_error():
            try:
                return self._my_errors.get(timeout=timeout)
            except queue.Empty:
                return None

        return None

    def is_error(self):
        an_error_if=not self._my_errors.empty()
        return an_error_if

    def error(self, id, errorCode, errorString):
        ## Overriden method
        errormsg = "IB error id %d errorcode %d string %s" % (id, errorCode, errorString)
        self._my_errors.put(errormsg)

    ## Position-related code
    def initPositions(self):
        self._positionsQueue = queue.Queue()
        return self._positionsQueue

    def position(self, account: str, contract: Contract, position: float,
                 avgCost: float):
        super().position(account, contract, position, avgCost)
        position = {
            'account': account,
            'contract': contract,
            'position': position,
            'avgCost': avgCost
        }
        self._positionsQueue.put(position)

    def positionEnd(self):
        super().positionEnd()
        print("PositionEnd")

class TestApp(TestWrapper, EClient):
    def __init__(self, ipaddress, portid, clientid):
        TestWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.init_error()

        self.connect(ipaddress, portid, clientid)

        thread = Thread(target = self.run)
        thread.start()

        setattr(self, "_thread", thread)



if __name__ == '__main__':
    ##
    ## Check that the port is the same as on the Gateway
    ## ipaddress is 127.0.0.1 if one same machine, clientid is arbitrary

    app = TestApp("127.0.0.1", 7497, 10)


    pos_storage = app.initPositions()

    ## Try and get a valid time
    MAX_WAIT_SECONDS = 10

    try:
        try:
            positions = pos_storage.get(timeout=MAX_WAIT_SECONDS)
            for pos in positions:
                print("Position.", pos['account'], "Symbol:", pos['contract'].symbol, "SecType:",
                      pos['contract'].secType, "Currency:", pos['contract'].currency,
                      "Position:", pos['position'], "Avg cost:", pos['avgCost'])

        except queue.Empty:
            print("Exceeded maximum wait for wrapper to respond")
            cds = None

        while app.wrapper.is_error():
            print(app.get_error())


    finally:
        app.disconnect()