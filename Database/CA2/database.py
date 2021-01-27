from SequentialBlocks import MainData
from BPlusTree import *
from Btree import *
from schema import *

class DataBase:
    def __init__(self, table_list):
        self.tables = table_list
        self.data = MainData(table_list)
        self.index = {}
        for i in table_list:
            temp_tree = BPlusTree(i, self.data.name[i].first)
            self.index[i] = temp_tree
            # also need a secondary index structure
            # like: self.second_index = {"PERSON": {"first_name":Btree1, "last_name":Btree2}, "Movie": {}, "Award":{}}
            self.data.name[i].BPlusTree = temp_tree
        self.second_index = {"PERSON":{"PERSON_first_name":Btree(), "PERSON_last_name": Btree(), "PERSON_year": Btree()},
                             "MOVIE":{"MOVIE_title": Btree(), "MOVIE_year": Btree(), "MOVIE_genre": Btree(), "MOVIE_country":Btree()},
                             "ROLE":{"ROLE_movie": Btree(), "ROLE_year": Btree()},
                             "RESTRICTION": {"RESTRICTION_description": Btree()},
                             "AWARD":{"AWARD_name":Btree(), "AWARD_country": Btree()},
                             "ACTOR_AWARD":{"ACTOR_AWARD_year":Btree(), "ACTOR_AWARD_result":Btree(), "ACTOR_AWARD_name":Btree()},
                             "DIRECTOR":{"DIRECTOR_title":Btree(), "DIRECTOR_year": Btree()},
                             "WRITER":{"WRITER_title":Btree(), "WRITER_year":Btree()}}

    def printTable(self, name):
        self.data.printTable(name)

    def get_BPlus_tree(self, name):
        return self.index[name]

    def search(self, name, key):
        tree = self.index[name]
        return tree.search(key)

    def search_attributes(self, name, input_dict):#attribute is a dictionary
        # primary key for PERSON, the input should be ("PERSON", {"id": "xxx"})
        # for table Movie, the input (primary key) should be ("Movie", {"title":"xxx", "year":"xxx"})
        # how to see if it's primary key or not?
        # get_info("Movie", ["year", "title"]) -> Info.prim_key = [0,1]; Info.attr = [1,0] -> it's primary key
        # WARNING, the input key may not be in order!!!!!
        # eg. for the key of "year" and "title" -> the input of search should be title, year -> make sure the order is OK
        # key might be primary key or secondary key
        # finally, the return value should be like [(xx,xx,xx,1,10,xx),(xx,xx,xx,1,10,xx),(xx,xx,xx,1,10,xx)]
        # a list of tuples satisfying conditions
        #first check if the attribute is primary key
        attribute = list(input_dict.keys())
        info = get_info(name, attribute)
        key_pos = info.key
        attr_pos = info.attr
        key_list = None
        if type(key_pos) == int and len(attr_pos) == 1 and key_pos == attr_pos[0]:#primary key
            tree = self.index[name]
            return tree.search(list(input_dict.values())[0])         
        elif type(key_pos) == list and type(attr_pos) == list:#primary key
            temp1 = key_pos
            temp2 = attr_pos
            temp1.sort()
            temp2.sort()    
            if temp1 == temp2:
                tree = self.index[name]
                helper_dict={}
                for i in range(len(attr_pos)):#sorted by attr_pos
                    list_keys = list(input_dict.values())
                    helper_dict[attr_pos[i]] = list_keys[i]
                    res_dict=dict(sorted(helper_dict.items()))
                    key_list = list(res_dict.values())
                return tree.search(key_list)
            else:
                return(self.find_by_btree(name, input_dict))
        else:
            return(self.find_by_btree(name, input_dict))
        #secondary key

    def find_by_btree(self, name, input_dict):
        # print(input_dict)
        schema = self.second_index[name]
        tot_i = []
        for i in input_dict:
            if not i in self.second_index[name].keys():
                temp = self.find_by_Maindata(name, input_dict[i])
            else:
                temp = schema[i].find(input_dict[i])#need changes
            tot_i += temp
        values = list(input_dict.values())
        temp = []
        for item in tot_i:#delete tuples that do not satisfy request 
            flag = 1
            for value in values:
                if not value in item:
                    flag = 0
            if flag == 1:
                temp.append(item)
        tot_i =temp
        tot_f = []
        for item in tot_i:# delete repeated tuple
            if tot_f.count(item) < 1:
                tot_f.append(item)
        return tot_f

    def find_by_Maindata(self, name, key):
        res = []
        L_list = self.data.name[name]
        for cursor in L_list:
            for item in cursor.tuples+cursor.overflowblock:
                if item != None and key in item:
                    res.append(item)
        return res

    def insert(self, name, tuple):
        res = self.data.insert(name, tuple, 0)
        if res == None:
            pass
        else:
            # print(res[1])
            new_block = res[0]
            new_key = res[1]
            tree = self.index[name]
            tree.insert(new_key, new_block)
        if name in self.second_index.keys():
            Btree_info = self.second_index[name]
            for i in Btree_info.keys():
                attr_pos = get_info(name, i).attr
                assert(type(attr_pos) is int)
                Btree_info[i].insert(tuple[attr_pos], tuple)
        return

    def delete(self, name, key):
        # key might be primary key or not
        if name in self.second_index.keys():
            for second_key,btree in self.second_index[name].items():
                second_key_pos = get_info(name, second_key).attr
                target_tuple = self.search(name, key)
                second_key_val = target_tuple[second_key_pos]
                btree.deleteRecord(second_key_val, target_tuple)
        res = self.data.delete(name, key, 0)
        tree = self.index[name]
        if res[0] is not None:
            tree.delete(res[0])
        if res[1] is not None:
            # res[1] is [block, key] from split
            # insert needs key, block
            tree.insert(res[1][1],res[1][0])

    def getListName(self):
        return self.tables

    def getSchema(self,name):
        schema_list = relation_schema[name]["schema"]
        ans = {}
        index = 0
        for i in schema_list:
            ans[i] = index
            index += 1
        return ans

    def getList(self, name):
        relation = self.data.name[name]
        ans = []
        for cursor in relation:
            for i in cursor.tuples:
                if i is not None:
                    ans.append(i)
            for j in cursor.overflowblock:
                if j is not None:
                    ans.append(j)
        return ans

if __name__ == "__main__":
    table_list = ["PERSON", "MOVIE"]
    database = DataBase(table_list)
    database.insert("PERSON", ('00001001', 'James', 'Stewart', 1908))
    database.insert("PERSON", ('00001002', 'Grace', 'Kelly', 1929))
    database.insert("PERSON", ('00001003', 'Raymond', 'Burr', 1917))
    database.insert("PERSON", ('00001004', 'John Michael', 'Hayes', 1919))
    database.insert("PERSON", ('00000982', 'Delia', 'Ephron', 1943))
    database.insert("PERSON", ('00000983', 'Lisa', 'Kudrow', 1963))
    database.insert("PERSON", ('00000961', 'Taylor', 'Hackford', 1945))
    database.insert("PERSON", ('00000700', 'Taylor', 'Swift', 1989))
    database.insert("PERSON", ('00000962', 'Tony', 'Gilroy (I)', 1962))
    database.insert("PERSON", ('00000963', 'David', 'Morse', 1953))
    database.insert("PERSON", ('00000941', 'John', 'Lasseter', 1957))
    database.insert("PERSON", ('00000903', 'Spencer', 'Breslin', 1992))
    database.insert("PERSON", ('00000904', 'Emily', 'Mortimer', 1971))
    database.insert("PERSON", ('00000881', 'Michael', 'Bay', 1965))
    database.insert("PERSON", ('00000882', 'Robert', 'Roy Pool', 1957))
    database.insert("PERSON", ('00001089','Andy','Carcia',1956))
    database.insert("PERSON", ('00001090','Nancy','Travis',1961))
    database.insert("PERSON", ('00001091','Frank','Mancuso',1958))
    database.insert("PERSON", ('00001092','John','Alonzo',1934))
    database.insert("PERSON", ('00001093','Robert','Estrin',1942))
    database.insert("PERSON", ('00001094','Carrie','Frazier',1947))
    database.insert("PERSON", ('00001095','Rudy','Dillon',1950))
    database.insert("PERSON", ('00001096','Barbet','Schroeder',1941))
    database.insert("PERSON", ('00001097','John','Lutz',1948))
    database.insert("PERSON", ('00001098','Bridget','Fonda',1964))
    database.insert("PERSON", ('00001099','Jennifer','Leigh',1962))
    database.insert("PERSON", ('00001100','Steven','Weber',1961))
    database.insert("PERSON", ('00001101','Luciano','Tovoli',1965))
    database.insert("PERSON", ('00001102','Lee','Percy',1971))
    database.insert("PERSON", ('00001104','Hal','Hartley',1959))
    database.insert("PERSON", ('00001105','Adrienne','Shelly',1966))
    # this is the test of searching with B tree -> secondary key
    print(database.search_attributes("PERSON", {"PERSON_first_name":'Lee'}))
    print(database.search_attributes("PERSON", {"PERSON_first_name": 'Taylor', "PERSON_year": 1989}))
    # first test
    database.data.printall("PERSON")
    print(database.data.name["PERSON"].numItems)
    print(database.index["PERSON"].root.keys)
    print(database.search("PERSON", '00000963'))
    print("checking root")
    print(database.index["PERSON"].root.keys)
    print("root's layer:", database.index["PERSON"].root.layer)
    print(database.index["PERSON"].root.children)
    print("checking next layer")
    for i in database.index["PERSON"].root.children:
        i.show()
        print("-------------")
    print("\ntesting delete\n")
    print("first checking the keys")
    for i in database.index["PERSON"].root.keys:
        print(i)
    print("#####delete things#####")
    database.delete("PERSON", '00000982')
    for i in database.index["PERSON"].root.children:
        i.show()
        print("-------------")
    print("delete again!!!!")
    database.delete("PERSON", '00000983')
    print("Let's see what happens!!!")
    for i in database.index["PERSON"].root.children:
        i.show()
        print("-------------")
    print("\nfinished the first test\n")
    database.insert("PERSON", ('00001106','Martin','Donovan',1957))
    database.insert("PERSON", ('00001107','Michael','Spiller',1961))
    database.insert("PERSON", ('00001108','Nick','Gomez',1963))
    database.insert("PERSON", ('00001109','Claudia','Brown',1962))
    database.insert("PERSON", ('00001110','Yimou','Zhang',1951))
    database.insert("PERSON", ('00001111','Heng','Liu',1964))
    database.insert("PERSON", ('00001112','Li','Gong',1965))
    database.insert("PERSON", ('00001113','Baotian','Li',1950))
    database.insert("PERSON", ('00001114','Hu','Jian',1962))
    database.insert("PERSON", ('00001115','Changwei','Gu',1965))
    database.insert("PERSON", ('00001116','Yuan','Du',1955))
    database.insert("PERSON", ('00001117','Zhi-an','Zhang',1963))
    database.insert("PERSON", ('00001118','Su','Tong',1957))
    database.insert("PERSON", ('00001119','Jingwu','Ma',1947))
    database.insert("PERSON", ('00001120','Caifei','He',1965))
    database.insert("PERSON", ('00001121','Fu-Sheng','Chiu',1956))
    database.insert("PERSON", ('00001122','Zhao','Fei',1952))
    database.insert("PERSON", ('00001123','Yuan','Du',1967))
    database.insert("PERSON", ('00001124','Jean-Paul','Rappeneau',1932))
    database.insert("PERSON", ('00001125','Gerard','Depardieu',1948))
    database.insert("PERSON", ('00001126','Anne','Brochet',1966))
    database.insert("PERSON", ('00001127','Rene','Cleitman',1940))
    # second test
    print("Let's see what happens!!!!")
    print("What's in main data? Using linear search first!\n")
    database.data.printall("PERSON")
    print("\nUse B+ tree to view data\n")
    print("How many blocks in one linked list?",database.data.name["PERSON"].numItems)
    print(database.index["PERSON"].root.keys)
    print("checking root")
    print(database.index["PERSON"].root.keys)
    print("root's layer:", database.index["PERSON"].root.layer)
    print(database.index["PERSON"].root.children)
    # print("checking next layer")
    for i in database.index["PERSON"].root.children:
        print("check layer", i.layer)
        print("check keys",i.keys)
        for j in i.children:
            j.show()
            print("see next block")
        print("----next children----")
    print("#####delete things#####")
    database.delete("PERSON", "00001108")
    print("this is the tree after this deletion")
    print(database.index["PERSON"].root.keys)
    for i in database.index["PERSON"].root.children:
        print("check layer", i.layer)
        print("check keys",i.keys)
        for j in i.children:
            j.show()
            print("see next block")
        print("----next children----")
    database.delete("PERSON", "00000904")
    database.delete("PERSON", "00000881")
    database.delete("PERSON", "00000882")
    database.delete("PERSON", "00000963")
    database.delete("PERSON", "00000962")
    database.delete("PERSON", "00001121")
    database.delete("PERSON", "00000961")
    print("this is the tree after this deletion")
    print(database.index["PERSON"].root.keys)
    for i in database.index["PERSON"].root.children:
        print("check layer", i.layer)
        print("check keys",i.keys)
        for j in i.children:
            j.show()
            print("see next block")
        print("----next children----")
    database.delete("PERSON", "00001109")
    print("this is the tree after this deletion")
    print(database.index["PERSON"].root.keys)
    for i in database.index["PERSON"].root.children:
        print("check layer", i.layer)
        print("check keys",i.keys)
        for j in i.children:
            j.show()
            print("see next block")
        print("----next children----")
    print("\nfinished the second test\n")
    database.insert("PERSON", ('00001128','Pierre','Lhomme',1930))
    database.insert("PERSON", ('00001129','Noelle','Boisson',1942))
    database.insert("PERSON", ('00001130','Franca','Squarciapion',1943))
    database.insert("PERSON", ('00001131','Diane','Keaton',1946))
    database.insert("PERSON", ('00001132','Robert','Rodriguez',1968))
    database.insert("PERSON", ('00001133','Carlos','Gallardo',1966))
    database.insert("PERSON", ('00001134','Consuelo','Gomez',1958))
    database.insert("PERSON", ('00001135','Lee','Tamahori',1950))
    database.insert("PERSON", ('00001136','Riwia','Brown',1953))
    database.insert("PERSON", ('00001137','Rena','Owen',1960))
    database.insert("PERSON", ('00001138','Temuera','Morrison',1961))
    database.insert("PERSON", ('00001139','Robin','Scholes',1965))
    database.insert("PERSON", ('00001140','Stuart','Dryburgh',1952))
    database.insert("PERSON", ('00001141','D.Michael','Horton',1958))
    database.insert("PERSON", ('00001142','Don','Selwyn',1960))
    database.insert("PERSON", ('00001143','Antonia','Bird',1963))
    database.insert("PERSON", ('00001144','Jimmy','McGovern',1949))
    database.insert("PERSON", ('00001145','Linus','Roache',1964))
    database.insert("PERSON", ('00001146','Tom','Wilkinson',1959))
    database.insert("PERSON", ('00001147','George','Faber',1961))
    database.insert("PERSON", ('00001148','Fred','Tammes',1963))
    database.insert("PERSON", ('00001149','Susan','Spivey',1957))
    database.insert("PERSON", ('00001150','Janet','Goddard',1965))
    database.insert("PERSON", ('00001151','Allan','Moyle',1947))
    database.insert("PERSON", ('00001152','Christian','Slater',1969))
    database.insert("PERSON", ('00001153','Samantha','Mathis',1970))
    database.insert("PERSON", ('00001154','Sandy','Stern',1968))
    database.insert("PERSON", ('00001155','Walt','Lloyd',1972))
    database.insert("PERSON", ('00001156','Larry','Bock',1962))
    database.insert("PERSON", ('00001157','Judith','Holstra',1964))
    database.insert("PERSON", ('00001158','Jeremiah S.','Chechik',1962))
    database.insert("PERSON", ('00001159','Barry','Berman',1957))
    database.insert("PERSON", ('00001160','Johnny','Depp',1963))
    database.insert("PERSON", ('00001161','Mary','Masterson',1966))
    database.insert("PERSON", ('00001162','John','Schwartzman',1965))
    database.insert("PERSON", ('00001163','Carol','Littleton',1957))
    database.insert("PERSON", ('00001164','Risa','Garcia',1956))
    database.insert("PERSON", ('00001165','Fred','Schepisi',1939))
    database.insert("PERSON", ('00001166','John','Guare',1938))
    database.insert("PERSON", ('00001167','Stockard','Channing',1944))
    database.insert("PERSON", ('00001168','Will','Smith',1968))
    database.insert("PERSON", ('00001169','Donald','Sutherland',1935))
    database.insert("PERSON", ('00001170','Ian','Baker',1947))
    database.insert("PERSON", ('00001171','Peter','Honess',1951))
    database.insert("PERSON", ('00001172','Ellen','Chenoweth',1962))
    database.insert("PERSON", ('00001173','Kaige','Chen',1952))
    database.insert("PERSON", ('00001174','Lillian','Lee',1954))
    database.insert("PERSON", ('00001175','Leslie','Cheung',1956))
    database.insert("PERSON", ('00001176','Fengyi','Zhang',1965))
    database.insert("PERSON", ('00001177','Feng','Hsu',1948))
    database.insert("PERSON", ('00001178','Xiaonan','Pei',1966))
    database.insert("PERSON", ('00001179','Wolfgang','Petersen',1941))
    database.insert("PERSON", ('00001180','Jeff','Maguire',1948))
    database.insert("PERSON", ('00001181','Clint','Eastwood',1930))
    database.insert("PERSON", ('00001182','John','Malkovich',1953))
    database.insert("PERSON", ('00001183','Rene','Russo',1954))
    database.insert("PERSON", ('00001184','John','Bailey',1942))
    database.insert("PERSON", ('00001185','Janet','Hirshenson',1950))
    database.insert("PERSON", ('00001186','Peter','Jackson',1961))
    database.insert("PERSON", ('00001187','Melanie','Lynskey',1977))
    database.insert("PERSON", ('00001188','Kate','Winslet',1975))
    database.insert("PERSON", ('00001189','Alun','Bollinger',1963))
    database.insert("PERSON", ('00001190','Jamie','Selkirk',1966))
    database.insert("PERSON", ('00001191','Steve','James',1957))
    database.insert("PERSON", ('00001192','William','Gates',1968))
    database.insert("PERSON", ('00001193','Arthur','Agee',1956))
    database.insert("PERSON", ('00001194','Peter','Gilbert',1963))
    database.insert("PERSON", ('00001195','David','Fincher',1962))
    database.insert("PERSON", ('00001196','Andrew','Walker',1964))
    database.insert("PERSON", ('00001197','Morgan','Freeman',1937))
    database.insert("PERSON", ('00001198','Brad','Pitt',1963))
    database.insert("PERSON", ('00001199','Darius','Khondji',1956))
    database.insert("PERSON", ('00001200','Richard','Francis-Bruce',1948))
    database.insert("PERSON", ('00001201','Kerry','Barden',1951))
    database.insert("PERSON", ('00001202','Danny','Boyle',1956))
    database.insert("PERSON", ('00001203','John','Hodge',1964))
    database.insert("PERSON", ('00001204','Kerry','Fox',1966))
    database.insert("PERSON", ('00001205','Christopher','Eccleston',1964))
    database.insert("PERSON", ('00001206','Ewan','McGregor',1971))
    database.insert("PERSON", ('00001207','Andrew','Macdonald',1966))
    database.insert("PERSON", ('00001208','Brian','Tufano',1968))
    database.insert("PERSON", ('00001209','Masahiro','Hirakubo',1964))
    database.insert("PERSON", ('00001210','Lawrence','Kasdan',1949))
    database.insert("PERSON", ('00001211','Adam','Brooks',1956))
    database.insert("PERSON", ('00001212','Meg','Ryan',1961))
    database.insert("PERSON", ('00001213','Kevin','Kline',1947))
    database.insert("PERSON", ('00001214','Timothy','Hutton',1960))
    database.insert("PERSON", ('00001215','Owen','Roizman',1936))
    database.insert("PERSON", ('00001216','Joe','Hutshing',1947))
    database.insert("PERSON", ('00001217','Timothy','Balme',1964))
    database.insert("PERSON", ('00001218','Diana','Penalver',1967))
    database.insert("PERSON", ('00001219','Elizabeth','Moody',1957))
    database.insert("PERSON", ('00001220','Murray','Milne',1959))
    database.insert("PERSON", ('00001221','Kevin','Smith',1970))
    database.insert("PERSON", ('00001222','Marilyn','Ghigliotti',1971))
    database.insert("PERSON", ('00001223','Lisa','Spoonhauer',1968))
    database.insert("PERSON", ('00001224','David','Klein',1965))
    database.insert("PERSON", ('00001225','Ron','Howard',1954))
    database.insert("PERSON", ('00001226','Jim','Lovell',1928))
    database.insert("PERSON", ('00001227','Tom','Hanks',1956))
    database.insert("PERSON", ('00001228','Bill','Paxton',1955))
    database.insert("PERSON", ('00001229','Kevin','Bacon',1958))
    database.insert("PERSON", ('00001230','Brian','Grazer',1951))
    database.insert("PERSON", ('00001231','Dean','Cundey',1945))
    database.insert("PERSON", ('00001232','Quentin','Tarantino',1963))
    database.insert("PERSON", ('00001233','Harvey','Keitel',1939))
    database.insert("PERSON", ('00001234','Tom','Roth',1961))
    database.insert("PERSON", ('00001235','Michael','Madsen',1958))
    database.insert("PERSON", ('00001236','Sally','Menke',1962))
    database.insert("PERSON", ('00001237','Ronnie','Yeskel',1967))
    database.insert("PERSON", ('00001238','John','Travolta',1954))
    database.insert("PERSON", ('00001239','Samuel','Jackson',1948))
    database.insert("PERSON", ('00001240','Lawrence','Bender',1958))
    database.insert("PERSON", ('00001241','Ang','Lee',1954))
    database.insert("PERSON", ('00001242','Sihung','Lung',1968))
    database.insert("PERSON", ('00001243','Yu-Wen','Wang',1969))
    database.insert("PERSON", ('00001244','Chien-lien','Wu',1968))
    database.insert("PERSON", ('00001245','Kong','Hsu',1956))
    database.insert("PERSON", ('00001246','Jong','Lin',1969))
    database.insert("PERSON", ('00001247','Tim','Squyres',1962))
    database.insert("PERSON", ('00001248','Robert','Altman',1925))
    database.insert("PERSON", ('00001249','Andie','MacDowell',1958))
    database.insert("PERSON", ('00001250','Bruce','Davison',1946))
    database.insert("PERSON", ('00001251','Jack','Lemmon',1925))
    database.insert("PERSON", ('00001252','Cary','Brokaw',1951))
    database.insert("PERSON", ('00001253','Geraldine','Peroni',1954))
    database.insert("PERSON", ('00001254','Edward','Zwick',1952))
    database.insert("PERSON", ('00001255','Jim','Harrison',1937))
    database.insert("PERSON", ('00001256','Anthony','Hopkins',1937))
    database.insert("PERSON", ('00001257','Aidan','Quinn',1959))
    database.insert("PERSON", ('00001258','John','Toll',1962))
    database.insert("PERSON", ('00001259','Steven','Rosenblum',1963))
    database.insert("PERSON", ('00001260','Mary','Colquhoun',1939))
    database.insert("PERSON", ('00001261','Oliver','Stone',1946))
    database.insert("PERSON", ('00001262','Woody','Harrelson',1961))
    database.insert("PERSON", ('00001263','Juliette','Lewis',1973))
    database.insert("PERSON", ('00001264','Robert','Richardson',1964))
    database.insert("PERSON", ('00001265','Brain','Berdan',1958))
    database.insert("PERSON", ('00001266','Richard','Hornung',1950))
    database.insert("PERSON", ('00001267','John','Carpenter',1948))
    database.insert("PERSON", ('00001268','Michael','Luca',1951))
    database.insert("PERSON", ('00001269','Sam','Neil',1947))
    database.insert("PERSON", ('00001270','Jurgen','Prochnow',1941))
    database.insert("PERSON", ('00001271','Julie','Carmen',1960))
    database.insert("PERSON", ('00001272','Gary','Kibbe',1954))
    database.insert("PERSON", ('00001273','Edward','Warschilka',1949))
    database.insert("PERSON", ('00001274','Robert','Zemeckis',1952))
    database.insert("PERSON", ('00001275','Winston','Groom',1944))
    database.insert("PERSON", ('00001276','Robin','Wright',1966))
    database.insert("PERSON", ('00001277','Gary','Sinise',1955))
    database.insert("PERSON", ('00001278','Wendy','Finerman',1953))
    database.insert("PERSON", ('00001279','Don','Burgess',1957))
    database.insert("PERSON", ('00001280','Ellen','Lewis',1961))
    database.insert("PERSON", ('00001281','Denzel','Washington',1954))
    database.insert("PERSON", ('00001282','Angela','Bassett',1958))
    database.insert("PERSON", ('00001283','Barry','Brown',1952))
    database.insert("PERSON", ('00001284','Kenneth','Branagh',1960))
    database.insert("PERSON", ('00001285','Scott','Frank',1960))
    database.insert("PERSON", ('00001286','Emma','Thompson',1959))
    database.insert("PERSON", ('00001287','Lindsay','Doran',1948))
    database.insert("PERSON", ('00001288','Matthew','Leonetti',1952))
    database.insert("PERSON", ('00001289','Peter','Berger',1955))
    database.insert("PERSON", ('00001290','Gail','Levin',1960))
    database.insert("PERSON", ('00001291','Steven','Spielberg',1946))
    database.insert("PERSON", ('00001292','Michael','Crichton',1942))
    database.insert("PERSON", ('00001293','Laura','Dern',1967))
    database.insert("PERSON", ('00001294','Jeff','Goldblum',1952))
    database.insert("PERSON", ('00001295','Kathleen','Kennedy',1947))
    database.insert("PERSON", ('00001296','Michael','Kahn',1924))
    database.insert("PERSON", ('00001297','Amy','Heckerling',1954))
    database.insert("PERSON", ('00001298','Alicia','Silverston',1976))
    database.insert("PERSON", ('00001299','Stacey','Dash',1966))
    database.insert("PERSON", ('00001300','Brittany','Murphy',1977))
    database.insert("PERSON", ('00001301','Scott','Rudin',1958))
    database.insert("PERSON", ('00001302','Bill','Pope',1961))
    database.insert("PERSON", ('00001303','Debra','Chiate',1970))
    database.insert("PERSON", ('00001304','Marcia','Ross',1969))
    database.insert("PERSON", ('00001305','Richard','Attenborough',1923))
    database.insert("PERSON", ('00001306','William','Nicholson',1948))
    database.insert("PERSON", ('00001307','Debra','Winger',1955))
    database.insert("PERSON", ('00001308','Roddy','Maude-Roxby',1930))
    database.insert("PERSON", ('00001309','Roger','Pratt',1947))
    database.insert("PERSON", ('00001310','Lesley','Walker',1956))
    database.insert("PERSON", ('00001311','Lucy','Boulting',1967))
    database.insert("PERSON", ('00001312','Isabelle','Huppert',1955))
    database.insert("PERSON", ('00001313','Elina','Lowensohn',1966))
    database.insert("PERSON", ('00001314','Steven','Hamilton',1968))
    database.insert("PERSON", ('00001315','Billy','Hopkins',1965))
    database.insert("PERSON", ('00001316','Alexandra','Welker',1959))
    database.insert("PERSON", ('00001317','Martin','Scorsese',1942))
    database.insert("PERSON", ('00001318','Robert','Niro',1943))
    database.insert("PERSON", ('00001319','Ray','Liotta',1955))
    database.insert("PERSON", ('00001320','Joe','Pesci',1943))
    database.insert("PERSON", ('00001321','Irwin','Winkler',1931))
    database.insert("PERSON", ('00001322','Michael','Ballhaus',1935))
    database.insert("PERSON", ('00001323','Thelma','Schoonmaker',1940))
    database.insert("PERSON", ('00001324','Gillian','Armstrong',1950))
    database.insert("PERSON", ('00001325','Lousia','Alcott',1832))
    database.insert("PERSON", ('00001326','Gabriel','Byrne',1950))
    database.insert("PERSON", ('00001327','Trini','Alvarado',1967))
    database.insert("PERSON", ('00001328','Denise','DiNovi',1955))
    database.insert("PERSON", ('00001329','Geoffrey','Simpson',1961))
    database.insert("PERSON", ('00001330','Nicholas','Beauman',1965))
    database.insert("PERSON", ('00001331','Jon','Turteltaub',1964))
    database.insert("PERSON", ('00001332','Daniel','Sullivan',1939))
    database.insert("PERSON", ('00001333','Sandra','Bullock',1964))
    database.insert("PERSON", ('00001334','Bill','Pullman',1953))
    database.insert("PERSON", ('00001335','Roger','Birnbaum',1954))
    database.insert("PERSON", ('00001336','Bruce','Green',1952))
    database.insert("PERSON", ('00001337','Cathy','Sandrich',1961))
    # test 3
    print(database.index["PERSON"].root.keys)
    for i in database.index["PERSON"].root.children:
        print(i.keys)
        for j in i.children:
            print("     ", j.keys)
            assert(j.layer is disk_layer)
    print(database.search("PERSON", "00001168"))
    print(database.search("PERSON", "00001317"))
    print("\nfinished the third test\n")
    database.insert("MOVIE", ('Titanic',1997,'USA',195,'romance'))
    database.insert("MOVIE", ('Shakespeare in Love',1998,'UK',122,'romance'))
    database.insert("MOVIE", ('The Cider House Rules',1999,'USA',125,'drama'))
    database.insert("MOVIE", ('Gandhi',1982,'India',188,'drama'))
    database.insert("MOVIE", ('American Beauty',1999,'USA',121,'drama'))
    database.insert("MOVIE", ('Affliction',1997,'USA',113,'drama'))
    database.insert("MOVIE", ('Life is Beautiful',1997,'Italy',118,'comedy'))
    database.insert("MOVIE", ('Boys Dont Cry',1999,'USA',118,'drama'))
    database.insert("MOVIE", ('Saving Private Ryan',1998,'USA',170,'action'))
    database.insert("MOVIE", ('The Birds',1963,'USA',119,'horror'))
    database.insert("MOVIE", ('The Matrix',1999,'USA',136,'action'))
    database.insert("MOVIE", ('Toy Story',1995,'USA',81,'animation'))
    database.insert("MOVIE", ('You have Got Mail',1998,'USA',119,'comedy'))
    database.insert("MOVIE", ('Proof of Life',2000,'USA',135,'drama'))
    database.insert("MOVIE", ('Hanging Up',2000,'USA',94,'comedy'))
    database.insert("MOVIE", ('The Price of Milk',2000,'New Zealand',87,'romance'))
    database.insert("MOVIE", ('The Footstep Man',1992,'New Zealand',89,'drama'))
    database.insert("MOVIE", ('Topless Women Talk About Their Lives',1997,'New Zealand',87,'drama'))
    database.insert("MOVIE", ('The Piano',1993,'New Zealand',121,'romance'))
    database.insert("MOVIE", ('Mad Max',1979,'Australia',88,'action'))
    database.insert("MOVIE", ('Strictly Ballroom',1992,'Australia',94,'comedy'))
    database.insert("MOVIE", ('My Mother Frank',2000,'Australia',95,'comedy'))
    database.insert("MOVIE", ('American Psycho',2000,'Canada',101,'horror'))
    database.insert("MOVIE", ('Scream 2',1997,'USA',116,'horror'))
    database.insert("MOVIE", ('Scream 3',2000,'USA',116,'horror'))
    database.data.printall("MOVIE")
    print(database.search_attributes("MOVIE", {"MOVIE_year":1999, "MOVIE_country": 'USA'}))
    database.printTable("PERSON")

