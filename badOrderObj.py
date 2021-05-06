class badOrderObj:
    def __init__(self, orderID, name, zipcode, illegalItem):
        self.orderID = orderID
        self.name = name
        self.zipcode = zipcode
        self.illegalItem = illegalItem

    def setOrderID(self, ID):
        self.orderID = id

    def setName(self, n):
        self.name = n

    def setZipcode(self, zip):
        self.zipcode = zip

    def setIllegalItem(self, illegal):
        self.illegalItem = illegal

    def getOrderID(self):
        return self.orderID

    def getName(self):
        return self.name

    def getZipcode(self):
        return self.zipcode

    def getIllegalItem(self):
       return self.illegalItem