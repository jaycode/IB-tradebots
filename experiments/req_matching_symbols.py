"""
https://interactivebrokers.github.io/tws-api/matching_symbols.html#gsc.tab=0
"""
from ibapi.wrapper import EWrapper, Contract
from ibapi.client import EClient
from threading import Thread
import queue

class TestWrapper(EWrapper):
    """
    The wrapper deals with the action coming back from the IB gateway or TWS instance

    We override methods in EWrapper that will get called when this action happens, like currentTime


    """

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

    ## Contract-related code
    def init_contract(self):
        contract_queue=queue.Queue()
        self._contract_queue = contract_queue

        return contract_queue

    def init_contract_descriptions(self):
        contract_descriptions_queue=queue.Queue()
        self._contract_descriptions_queue = contract_descriptions_queue

        return contract_descriptions_queue

    def contractDetails(self, req_id, contract_details):
        self._contract_queue.put((req_id, contract_details))

    def symbolSamples(self, req_id, contract_descriptions):
        print("symbolSamples. request id: ", req_id)
        self._contract_descriptions_queue.put(contract_descriptions)


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


    cd_storage = app.init_contract_descriptions()
    req_id = 1
    app.reqMatchingSymbols(req_id, "SPY")

    ## Try and get a valid time
    MAX_WAIT_SECONDS = 10

    try:
        try:
            cds = cd_storage.get(timeout=MAX_WAIT_SECONDS)
            for cd in cds:
                derivSecTypes = ""
                for derivSecType in cd.derivativeSecTypes:
                    derivSecTypes += derivSecType
                    derivSecTypes += " "
                print(("Contract: conId:{}, symbol:{}, secType:{} primExchange:{}, " +
                      "currency: {}, derivativeSecTypes:{}").format(
                    cd.contract.conId,
                    cd.contract.symbol,
                    cd.contract.secType,
                    cd.contract.primaryExchange,
                    cd.contract.currency,
                    derivSecTypes
                    )
                )
        except queue.Empty:
            print("Exceeded maximum wait for wrapper to respond")
            cds = None

        while app.wrapper.is_error():
            print(app.get_error())


    finally:
        app.disconnect()