# this is the Abstract Stack Machine

import pysnooper
from database import DataBase
from schema import *

class Stack(object):
    class Node(object):
        def __init__(self, val):
            self.val = val
            self.next = None

    def __init__(self):
        self.first = None

    def top(self):
        if self.first is not None:
            return self.first.val
        else:
            return None

    def push(self, n):
        n = self.Node(n)
        n.next = self.first
        self.first = n
        return n.val

    def pop(self):
        if self.first is None:
            return None
        else:
            tmp = self.first.val
            self.first = self.first.next
            return tmp

    def isEmpty(self):
        if None == self.top():
            return True
        else:
            return False

    def showData(self):
        if self.first is None:
            return
        temp = self.first
        while temp is not None:
            print(temp.val)
            temp = temp.next

    def __iter__(self):
        if self.first is None:
            return
        temp = self.first
        while temp is not None:
            yield temp.val
            temp = temp.next

    def clear(self):
        self.first = None

class ASM:
    def __init__(self, db):
        self.database = db
        self.RES = Stack()
        self.ENV = Stack()
        self.unitaryOperatorDic = {"count":self.Count,"sum":self.Sum,"min":self.Min,"max":self.Max,"average":self.Average,"distinct":self.Distinct,"not":self.Not}
        self.binaryOperatorDic = {"<":self.Less,">":self.Larger,"<=":self.NotLarger,">=":self.NotLess,"==":self.Equal,"neq":self.NotEqual,"+":self.Add,"-":self.Minus,"*":self.Times,"/":self.Divide,"and":self.And,"or":self.Or,"in":self.In,"cross":self.Cross,"search":self.search,"=":self.assign}
        self.binaryKeyWord = ["<",">","<=",">=","==","=","neq","+","-","*","/","and","or","in","cross","search"]
        self.unitaryKeyWord = ["count","sum","min","max","average","distinct","not"]
        self.variables = {}
        self.varschema = {}

    # you could input a 0 in order not print out the result
    # the default is to print
    def Run(self, query, optional = 1):
        stringList = self.DealWithBracket(query,0)[0]
        self.Execute(stringList, (), {})
        result = self.RES.pop()
        self.ENV.clear()
        if optional == 1:
            print(result)
        return result

    #@pysnooper.snoop()
    def Execute(self, query, entry, schema):
        i = 0
        while(i<len(query)):
            item = query[i]
            if(type(item)==str):
                if item == "where":
                    result = []
                    iterator = self.RES.pop()
                    schema = self.ENV.pop()
                    for entry in iterator:
                        self.Execute(query[i+1], entry, schema)
                        if self.RES.pop():
                            result.append(entry)
                    self.ENV.push(schema)
                    self.RES.push(result)
                    i +=2
                elif(self.CheckKeyWord(item)[0]):
                    if(self.CheckKeyWord(item)[1]):
                        self.Execute(query[i+1], entry, schema)
                        operand = self.RES.pop()
                        result = self.unitaryOperatorDic[item](operand)
                        self.RES.push(result)
                        i +=2
                    else:
                        if(type(query[i+1])==str):
                            self.query(query[i+1], entry, schema)
                        else:
                            self.Execute(query[i+1], entry, schema)
                        operand1 = self.RES.pop()
                        operand2 = self.RES.pop()
                        result = self.binaryOperatorDic[item](operand2,operand1)
                        self.RES.push(result)
                        i +=2
                else:
                    self.query(item, entry, schema)
                    i +=1
            else:
                self.Execute(item, entry, schema)
                i+=1
        return

    def DealWithBracket(self, string, index):
            stringList = []
            word = ""
            while(index<len(string) and string[index]!=")"):
                if(string[index]=="("):
                    (tempList,tempIndex) = self.DealWithBracket(string,index+1)
                    stringList.append(tempList)
                    index=tempIndex
                elif(string[index]==" "):
                    if(word!=''):
                        stringList.append(word)
                        word=""
                else:
                    word += string[index]
                index +=1
            stringList.append(word)
            for i in stringList:
                if(i==''):
                    stringList.remove(i)
            return (stringList,index)

    def CheckKeyWord(self, word):
        isFound = False
        isUnitary = False
        for i in self.binaryKeyWord:
            if(word==i):
                isFound = True
                break
        for i in self.unitaryKeyWord:
            if(word==i):
                isFound = True
                isUnitary = True
                break
        return (isFound,isUnitary)

    #@pysnooper.snoop()
    def query(self, string, entry, schema):
        try:
            a = float(string)
            self.RES.push(a)
        except:
            # Projection / Query from database:
            # 5 case 5 different way to get schema
            # case1:
            #   self.xxx
            #   get schema from parameter corresponding to "self"
            #   which is popped form ENV when begin a "where" loop
            #   and pushed into ENV when the "where" loop is end
            #   input from parameter self
            #   output the xxx of self
            #   i.e. self -> self.data
            # case2:
            #   (xxx).xxx
            #   get schema from the top of the ENV
            #   input from RES
            #   output a list of corresponding attribute
            #   i.e. [xxx1, xxx2, xxx3, ...] -> [xxx1.data, xxx2.data, xxx3.data, ...]
            # case3:
            #   var.xxx
            #   get schema form the schema dictionary of variables
            #   input from variable dictionary
            #   output a list of corresponding attribute
            #   i.e. [xxx1, xxx2, xxx3, ...] -> [xxx1.data, xxx2.data, xxx3.data, ...]
            # case4:
            #   MOVIE.xxx
            #   get schema directly from the database
            #   input from database
            #   output a list of corresponding attribute
            #   i.e. [MOVIE1, MOVIE2, MOVIE3, ...] -> [MOVIE1.data, MOVIE2.data, MOVIE3.data, ...]
            # case5:
            #   MOVIE
            #   get schema directly from the database
            #   push the schema into ENV after query
            #   input from database
            #   output a list of entry
            #   i.e. [MOVIE1, MOVIE2, MOVIE3, ...]
            #
            # case6:
            #   non-query string
            #   push into RES
            if string in self.variables:
                self.ENV.push(self.varschema[string])
                self.RES.push(self.variables[string])
            elif string[0] == "@":
                self.RES.push(string[1:])
            elif '.' in string:
                # A.B would be split into [A, B]
                # i.e. temp = [A, B]
                temp = string.split('.')
                # case1: self.xxx
                if temp[0] == "self":
                    result = entry[schema[temp[1]]]
                    self.RES.push(result)
                # case2: (xxx).xxx
                elif temp[0] == "":
                    schema = self.ENV.pop()
                    sorList = self.RES.pop()
                    result = []
                    for base in sorList:
                        result.append(base[schema[temp[1]]])
                    self.RES.push(result)
                # case3: var.xxx
                elif temp[0] in self.variables:
                    schema = self.varschema[temp[0]]
                    sorList = self.variables[temp[0]]
                    result = []
                    for base in sorList:
                        result.append(base[schema[temp[1]]])
                    self.RES.push(result)
                # case4: PERFORMANCE.xxx
                else:
                    schema = self.database.getSchema(temp[0])
                    sorList = self.database.getList(temp[0])
                    result = []
                    for base in sorList:
                        result.append(base[schema[temp[1]]])
                    self.RES.push(result)
            else:
                # case5: PERFORMANCE
                if string in self.database.getListName():
                    schema = self.database.getSchema(string)
                    result = self.database.getList(string)
                    self.ENV.push(schema)
                    self.RES.push(result)
                # case6: just string
                else:
                    self.RES.push(string)
            return

    def Count(self, operand):
        return len(operand)
    
    def Sum(self, operand):
        return sum(operand)

    def Min(self, operand):
        return min(operand)

    def Max(self, operand):
        return max(operand)

    def Average(self, operand):
        return sum(operand)/len(operand)

    def Distinct(self, operand):
        return list(set(operand))

    def Not(self, operand):
        return not operand

    def Less(self, operand1, operand2):
        return operand1 < operand2

    def Larger(self, operand1, operand2):
        return operand1 > operand2

    def NotLarger(self, operand1, operand2):
        return operand1 <= operand2

    def NotLess(self, operand1, operand2):
        return operand1 >= operand2

    def Equal(self, operand1, operand2):
        return operand1 == operand2

    def NotEqual(self, operand1, operand2):
        return operand1 != operand2

    def Add(self, operand1, operand2):
        return operand1 + operand2

    def Minus(self, operand1, operand2):
        return operand1 - operand2

    def Times(self, operand1, operand2):
        return operand1 * operand2

    def Divide(self, operand1, operand2):
        return operand1 / operand2

    def And(self, operand1, operand2):
        return operand1 and operand2

    def Or(self, operand1, operand2):
        return operand1 or operand2

    def In(self, operand1, operand2):
        return operand1 in operand2

    #@pysnooper.snoop()
    def Cross(self, operand1, operand2):
        schema2 = self.ENV.pop()
        schema1 = self.ENV.pop()
        temp = {}
        for i in schema2.items():
            temp[i[0]] = i[1] + len(schema1)
        newschema = schema1.copy()
        newschema.update(temp)
        self.ENV.push(newschema)
        result = []
        for entry1 in operand1:
            for entry2 in operand2:
                result.append(entry1+entry2)
        return result

    # It should only be used to assgin a table!
    # No processed list such as a list of IDs!
    def assign(self, name, table):
        if name in self.database.getListName():
            raise Exception("variable name should not be keyword!")
        else:
            schema = self.ENV.top()
            self.variables[name] = table
            self.varschema[name] = schema
            return table

    #@pysnooper.snoop()
    def search(self, name, string):
        # attribute is a dict consists of the attribute and the corresponding 
        # with the form: {attribute1:value1,attribute2:value2,...}
        attribute = eval(string)
        if name in self.database.getListName():
            result = self.database.search_attributes(name, attribute)
            schema = self.database.getSchema(name)
            self.ENV.push(schema)
            return result


if __name__ == "__main__":
    db = DataBase(list(relation_schema.keys()))
    a = ASM(db)
    '''
    "RESTRICTION_title", "RESTRICTION_year", "RESTRICTION_description", "RESTRICTION_country"
    '''
    db.insert("RESTRICTION",("a",1984,"R","USA"))
    db.insert("RESTRICTION",("a",1984,"R18","JP"))
    db.insert("RESTRICTION",("b",1988,"R","USA"))
    db.insert("RESTRICTION",("b",1988,"15","UK"))
    db.insert("RESTRICTION",("c",1999,"R","USA"))
    db.insert("RESTRICTION",("c",1988,"R18","UK"))

    '''
    "MOVIE_title", "MOVIE_year", "MOVIE_country", "MOVIE_runtime", "MOVIE_genre"
    '''
    db.insert("MOVIE",("a",1984,"USA",180,"action"))
    db.insert("MOVIE",("b",1988,"UK",200,"comedy"))
    db.insert("MOVIE",("c",1999,"JP",90,"scary"))
    db.insert("MOVIE",("c",1988,"USA",90,"comedy"))

    '''
    "ROLE_id", "ROLE_movie", "ROLE_year", "ROLE_description", "ROLE_credits"
    '''
    db.insert("ROLE",(1,"a",1984,"friendA"))
    db.insert("ROLE",(2,"a",1984,"py"))
    db.insert("ROLE",(1,"b",1988,"yyut"))
    db.insert("ROLE",(3,"b",1988,"yyyy"))
    db.insert("ROLE",(3,"c",1999,"yyut"))
    db.insert("ROLE",(4,"c",1988,"py"))
    '''
    "PERSON_id", "PERSON_first_name", "PERSON_last_name", "PERSON_year"
    '''
    db.insert("PERSON",(1,"Xie","Tian",1999))
    db.insert("PERSON",(2,"Zhu","Zhongbo",1999))
    db.insert("PERSON",(3,"Yuan","Yue",2001))
    db.insert("PERSON",(4,"Zhang","Junkai",2000))

    # the testing part
    print(db.getList("RESTRICTION"))
    print(db.getSchema("MOVIE"))
    print(db.getListName())

    print()
    # running queries
    a.Run("MOVIE where (self.MOVIE_year > 1987)")
    print()
    a.Run("1997 in MOVIE.MOVIE_year")
    print()
    # you'd better add bracket between two equal, here is just a coincident correct answer (but wrong grammar?)
    a.Run("(MOVIE cross RESTRICTION) where ((self.MOVIE_year == self.RESTRICTION_year) and (self.MOVIE_title == self.RESTRICTION_title))")
    # when operate (xxx).id, please add bracket
    print()
    a.Run("PERSON where (not (self.PERSON_id in ((((RESTRICTION where (self.RESTRICTION_description == R18)) cross ROLE) where (self.RESTRICTION_title == self.ROLE_movie and self.RESTRICTION_year == self.ROLE_year)).ROLE_id)))")