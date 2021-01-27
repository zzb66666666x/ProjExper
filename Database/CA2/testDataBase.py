###############################################################
#######################Ignore this file########################
###############################################################
# this is the testing database for the stack machine
# not the formal one
class TestDB():
    def __init__(self):
        self.data = {}
        self.schemas = {}

    def newList(self, name, schema):
        if not (name in self.schemas):
            self.schemas[name] = schema
            self.data[name] = []
        else:
            print("list exist")

    def addData(self, name, data):
        if name in self.schemas:
            self.data[name].append(data)
        else:
            print("list does not exist")

    def printAllData(self):
        for name in self.schemas:
            print(name)
            print("-"*40*len(self.schemas[name]))
            for attribute in self.schemas[name]:
                print("{:<40s}".format(attribute), end="")
            print("\n"+"-"*40*4)
            for entry in self.data[name]:
                for data in entry:
                    print("{:<40s}".format(str(data)), end="")
                print("")
            print("-"*40*len(self.schemas[name]))
            print("")

    def getList(self, name):
        return self.data[name]

    def getListName(self):
        return list(self.schemas.keys())

    def getSchema(self, name):
        return self.schemas[name]