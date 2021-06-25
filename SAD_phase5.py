import csv

WARNING = '\033[93m'
GREEN = "\033[92m"
RED = "\033[1;31m"
RESET = "\033[0;0m"
OKCYAN = '\033[96m'
HEADER = '\033[95m'

class Service:
    def __init__(self,serviceId,customerId,items):
        self.serviceId = serviceId
        self.customerId = customerId
        self.items = items

class TransportService(Service):
    def __init__(self,serviceId,customerId,time,items,srcAdr,destAdr,date):
        self.srcAdr = srcAdr
        self.destAdr = destAdr
        self.time = time
        self.date = date
        self.drivers = []

        Service.__init__(self,serviceId,customerId,items)

    def assignDriver(self,drivers):

        for drive in drivers:
            self.drivers.append(drive)

    def requestDriver(self,driverTimeTableCatalog,drivers):
        driverHandler = DriverHandler(self,driverTimeTableCatalog,drivers)
        print(WARNING + "Requested for a driver..." + RESET)
        availableDrivers = driverHandler.scheduleDrivers()
        if availableDrivers == -1:
            print(RED + "No driver available! try again later." + RESET)
            return False
        else:
            print("Drivers with id {} are available.".format(','.join(availableDrivers)))
            self.assignDriver(availableDrivers)
            print("The cargo will send from {} to {} in date {} at {}o'clock.".format(self.srcAdr,self.destAdr,self.date,self.time))
            driverHandler.notifyTransporter(availableDrivers)
            return True

        
class DriverHandler:
    def __init__(self,tpService,driverTimeTableCatalog,drivers):
        self.driverTimeTableCatalog = driverTimeTableCatalog
        self.drivers = drivers
        self.isBusy = [False] * len(self.drivers)
        self.drivers.sort(key=lambda x: x.vehicle.weightLimit, reverse=True)
        self.tpService = tpService
    
    def getDriverTimeTable(self,date):
        for driverTime in self.driverTimeTableCatalog.driverTimeTable:
            if driverTime.date == date:
                return driverTime
        return None

    def scheduleDrivers(self):
        sumWeight = sum(c.weight for c in self.tpService.items)
        sumSize = sum(c.volume for c in self.tpService.items)
        

        for driver in self.drivers:
            for entry in self.driverTimeTableCatalog.driverTimeTable:
                entryTime = int(entry.time.split(':')[0]) * 60 + int(entry.time.split(':')[1])
                tpTime = int(self.tpService.time.split(':')[0]) * 60 + int(self.tpService.time.split(':')[1])
                if entry.date == self.tpService.date and driver.driverId == entry.driverId and abs(entryTime - tpTime) < 60:
                    self.isBusy[driver.driverId] = True
            
        for driver in reversed(self.drivers):
            if self.isBusy[len(self.isBusy) - 1 - driver.driverId]: continue

            if sumWeight > driver.vehicle.weightLimit or sumSize > driver.vehicle.containerSize:
                continue

            return [str(driver.driverId)]

        whichDrivers = []
        driverIndex = 0
        while sumWeight > 0 or sumSize > 0:
            if driverIndex >= len(self.drivers): return -1
            if self.isBusy[driverIndex]:
                driverIndex += 1 
                continue
            sumWeight -= self.drivers[driverIndex].vehicle.weightLimit
            sumSize -= self.drivers[driverIndex].vehicle.containerSize
            whichDrivers.append(str(self.drivers[driverIndex].driverId))
            driverIndex += 1

        return whichDrivers
            
    def cancelDriver(self,driverId,serviceId):
        print("The driver {} has canceled service {}.".format(driverId,serviceId))
        print("finding new driver...")
        
        availableDrivers = self.scheduleDrivers()
        if availableDrivers == -1:
            print(RED + "No driver available! try again later." + RESET)
            return False
        else:
            print("Driver(s) with id {} is available".format(','.join(availableDrivers)))
            self.assignDriver(availableDrivers)
            print("The cargo will send from {} to {} in date {} at {}o'clock.".format(self.srcAdr,self.destAdr,self.date,self.time))
            self.notifyTransporter(availableDrivers)
            return True
        
    def notifyTransporter(self,availableDrivers):
        print("The transporter {} has been notified.".format(','.join(availableDrivers)))

class Driver:
    def __init__(self,driverId,car):
        self.driverId = driverId
        self.vehicle = car
    
    def acceptService(self, serviceId):
        print("Driver {} has accepted the service number {}.".format(self.driverId,serviceId))
        return True

    def declineService(self, serviceId):
        print("Driver {} has declined the service number {}.".format(self.driverId,serviceId))
        return False

class Car:
    def __init__(self,weightLimit,containerSize):
        self.weightLimit = weightLimit
        self.containerSize = containerSize

class DriverTimeTableCatalog:
    def __init__(self):
        self.driverTimeTable = []

    def sortTimeTable(self):
        self.driverTimeTable.sort(key=lambda x: x.date.split('/')[0], reverse=True)

    def insertEntry(self,entry):
        self.driverTimeTable.append(entry)

    def deleteEntry(self,entry):
        for en in range(len(self.driverTimeTable)):
            if self.driverTimeTable[en] == entry:
                self.driverTimeTable.remove(entry)
                break

    def modifyEntry(self,entry1,entry2):
        for en in range(len(self.driverTimeTable)):
            if self.driverTimeTable[en] == entry1:
                self.driverTimeTable[en] = entry2

class TimeTableEntry:
    def __init__(self,driverId,date,time) -> None:
        self.driverId, self.date, self.time = driverId, date, time

class System:
    customers = []
    services = []
    drivers = [Driver(i,Car(100,100)) for i in range(5)]
    driverCatalog = DriverTimeTableCatalog()
    serviceId = None
    customerId = 0

    def __init__(self,customers):
        self.customers = customers
        for i in range(len(self.customers)):
            self.customers[i].customerId = i
        
        self.readFromCsv()
        self.completeCatalog()


    def completeCatalog(self):
        for serv in self.services:
            for driv in serv.drivers:
                self.driverCatalog.insertEntry(TimeTableEntry(driv,serv.date,serv.time))

    def readFromCsv(self):
        row = None
        with open('services.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if len(row) == 0: return
                if line_count == 0:
                    line_count += 1
                else:
                    newTransportService = TransportService(row[0],row[1],row[5],None,row[2],row[3],row[4])
                    dirverIds = list(map(int,row[6].split('.')))
                    for i in dirverIds:
                        newTransportService.drivers.append(i)
                    self.services.append(newTransportService)
                    line_count += 1
        
        self.serviceId = int(row[0]) + 1

    def sendTransportForm(self):
        form = ['','','']
        return form
    
    def getTransactionInfo(self, paymentInfo):
        #get info from Shaparak
        shaparakInfo = paymentInfo
        paymentSuccess = (shaparakInfo == paymentInfo)
        if (paymentSuccess):
            return True
        else:
            return False

    def validateForm(self,customerId,time,items,form):
        if form[0] != "" and form[1] != "" and form[2] != "":
            print(GREEN + "Your form is valid. please proceed to payment.." + RESET)

            while (not self.getTransactionInfo('paymentInfo')):
                ans = input('payment failed. do you want to try again? [y/n]: ')
                if ans.strip() =='y' or ans.strip() == 'Y':
                    print("please proceed to payment")
                else:
                    print(RED + "your request has been canceled!" + RESET)
                    return
            print(GREEN + "Payment was Successful and your form has been submitted." + RESET)
            self.createTransportService(customerId,time,items,form)

        else: print(RED + "Your form is INVALID!")
    
    def createTransportService(self,customerId,time,items,form):
        newTransportService = TransportService(self.serviceId,customerId,time,items,form[0],form[1],form[2])
        requestSuccess = newTransportService.requestDriver(self.driverCatalog,self.drivers)
        if requestSuccess:
            self.updateDriverTimeTableCatalog(newTransportService)
            self.services.append(newTransportService)
            self.writeCsv(newTransportService)
            self.notifyCustomer(customerId)
            self.serviceId += 1
        return requestSuccess
    
    def writeCsv(self,tpService):
        with open('services.csv', mode='a',newline='') as serviceFile:
            services = csv.writer(serviceFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            drivers = '.'.join(str(id) for id in tpService.drivers)
            services.writerow([tpService.serviceId,tpService.customerId,tpService.srcAdr,tpService.destAdr,tpService.date,tpService.time,drivers])


    def notifyCustomer(self, customerId):
        print("Customer {} has been notified about the cargo.".format(customerId))

    def updateDriverTimeTableCatalog(self,newTransportService):
        for driv in newTransportService.drivers:
            self.driverCatalog.insertEntry(TimeTableEntry(driv,newTransportService.date,newTransportService.time))


class Item:
    def __init__(self,weight,volume):
        self.weight = int(weight)
        self.volume = int(volume)

class Customer:
    def __init__(self,firstName,lastName,adr,postalCode):
        self.firstName = firstName
        self.lastName = lastName
        self.address = adr
        self.postalCode = postalCode
        print(GREEN + "You successfully signed up!" + RESET)

    def requestTransportService(self,system):
        emptyForm = system.sendTransportForm()
        print(HEADER + "Write down your form..." + RESET)
        srcAdr = input(OKCYAN + "Source address: ")
        destAdr = input("Destination address: ")
        date = input("Date (MM/DD/YYYY): ")
        time = input("Time (HH:MM): ")
        n = int(input('Number of items: '))
        items = []
        for i in range(n):
            w = input("Your item " + str(i + 1) + " weight: ")
            v = input("Your item " + str(i + 1) + " volume: ")
            item = Item(w,v)
            items.append(item)
        print(RESET)
        fillForm = [srcAdr,destAdr,date]
        self.sendTransportForm(system,time,items,fillForm)
    
    def sendTransportForm(self,system,time,items,filledForm):
        system.validateForm(self.customerId,time,items,filledForm)

if __name__ == '__main__':
    customers = []

    print(HEADER + 'SIGN UP!' + RESET)
    firstName = input(OKCYAN + "Enter your first name: ")
    lastName = input("Enter your last name: ")
    adr = input("Enter your address: ")
    postCode = input("Enter your postal code: " + RESET)
    customer = Customer(firstName,lastName,adr,postCode)
    customers.append(customer)

    system = System(customers)

    while True:
        req = input(OKCYAN + "For requesting transportation, enter 1 (for ''exit'' enter 0): " + RESET)
        if req.strip() == '1': customer.requestTransportService(system)
        elif req.strip() == '0':
            print(HEADER + 'Thank you for choosing our service ;)' + RESET)
            quit(0)