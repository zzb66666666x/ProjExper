# New version of sequential storage written by Zhu Zhongbo and Yang Zhaohua
from schema import *

class MainData:
    class DLinkedList:
        class Block:
            def __init__(self, size, overflow_size, tuples = None, previous = None, next = None):
                self.tuples = []
                self.overflowblock = [None] * overflow_size
                self.next = next
                self.pre = previous
                self.numtuples = 0
                self.minimum = None
                self.maximum = None
                if tuples is not None:
                    assert(type(tuples) is list or type(tuples) is tuple)
                    for i in range(len(tuples)):
                        if tuples[i] is not None:
                            self.tuples[i] = tuples[i]
                            self.numtuples += 1

            def getnumtuples(self):
                return self.numtuples

            def find(self, key, get_key, eval_key):
                for item in self.overflowblock:
                    if get_key(item) == key:
                        return item
                maindata = []
                for item in self.tuples:
                    if item is not None:
                        maindata.append(item)
                key_val = eval_key(key)
                # print(maindata)
                # print(key_val)
                return self.__find(maindata, key_val, 0, len(maindata)-1, get_key, eval_key)

            def __find(self, maindata, target_key_val, left, right, get_key, eval_key):
                # print(target_key_val)
                if left > right:
                    return None
                med = (left + right)//2
                med_tuple = maindata[med]
                # print(med_tuple)
                med_key = get_key(med_tuple)
                med_key_val = eval_key(med_key)
                if med_key_val == target_key_val:
                    return med_tuple
                elif med_key_val > target_key_val:
                    return self.__find(maindata, target_key_val, left, med-1, get_key, eval_key)
                else:
                    return self.__find(maindata, target_key_val, med+1, right, get_key, eval_key)

            def insert(self, tuple, get_key, eval_key):
                # insert to overflow
                key_val = eval_key(get_key(tuple))
                if self.maximum is None or self.minimum is None:
                    self.maximum = key_val
                    self.minimum = key_val
                elif key_val > self.maximum:
                    self.maximum = key_val
                elif key_val < self.minimum:
                    self.minimum = key_val
                for i in range(len(self.overflowblock)):
                    if self.overflowblock[i] is None:
                        self.overflowblock[i] = tuple
                        self.numtuples += 1
                        return True
                raise Exception("full overflow block")

            def is_overflowblock_full(self):
                flag = True
                for i in self.overflowblock:
                    if i is None:
                        flag = False
                return flag

            def include(self, key, get_key):
                for item in self.tuples:
                    if get_key(item) == key:
                        return True
                for item in self.overflowblock:
                    if get_key(item) == key:
                        return True
                return False

            def maintain_bounds(self, get_key, eval_key):
                maximum = eval_key(get_key(self.tuples[0]))
                minimum = eval_key(get_key(self.tuples[0]))
                for temp in [self.tuples, self.overflowblock]:
                    for i in temp:
                        temp_key = eval_key(get_key(i))
                        if temp_key is None:
                            continue
                        if maximum is None:
                            maximum = temp_key
                            continue
                        if minimum is None:
                            minimum = temp_key
                            continue
                        if temp_key > maximum:
                            maximum = temp_key
                        if temp_key < minimum:
                            minimum = temp_key
                self.maximum = maximum
                self.minimum = minimum

            def get_bounds(self):
                return self.maximum,self.minimum

            def find_min_key(self, get_key, eval_key):
                min_key = None
                min_key_val = None
                for item in self.tuples:
                    if item != None:
                        if min_key is None:
                            min_key = get_key(item)
                            min_key_val = eval_key(min_key)
                        else:
                            key = get_key(item)
                            key_val = eval_key(key)
                            if key_val <= min_key_val:
                                min_key = key
                                min_key_val = key_val
                for item in self.overflowblock:
                    if item != None:
                        if min_key is None:
                            min_key = get_key(item)
                            min_key_val = eval_key(min_key)
                        else:
                            key = get_key(item)
                            key_val = eval_key(key)
                            if key_val <= min_key_val:
                                min_key = key
                                min_key_val = key_val
                return min_key

            def show(self):
                for i in self.tuples:
                    if i is not None:
                        print(i)
                print("----")
                for i in self.overflowblock:
                    if i is not None:
                        print(i)

        def __init__(self, blocksize, overflow_size, get_key, eval_key):
            self.blocksize = blocksize
            self.overflow_size = overflow_size
            self.first = MainData.DLinkedList.Block(blocksize, overflow_size)
            self.numItems = 1
            self.first.next = None
            self.first.pre = None
            self.last = self.first
            self.get_key = get_key
            self.eval_key = eval_key
            self.BPlusTree = None

        def __iter__(self):
            cursor = self.first
            while cursor != None:
                yield cursor
                cursor = cursor.next

    # the functions for main data: IO functions here
    def __init__(self, table_list, blocksize = 12, overflow_size = 4):
        self.blocksize = blocksize
        self.overflow_size = overflow_size
        self.name = {}
        for i in table_list:
            self.name[i] = MainData.DLinkedList(blocksize, overflow_size, get_key_table[i], eval_key_string)
        self.tables = table_list

    def find(self, name, key):
        if name not in self.tables:
            return None
        relation = self.name[name]
        eval_key = relation.eval_key
        get_key = relation.get_key
        key_val = eval_key(key)
        for block in relation:
            if not (block.minimum <= key_val <= block.maximum):
                continue
            return block.find(key, get_key, eval_key)

    def insert(self, name, tuple, linear_search=1):
        if name not in self.tables:
            return None
        relation = self.name[name]
        eval_key = relation.eval_key
        get_key = relation.get_key
        key = get_key(tuple)
        # print(relation.numItems)
        # print(relation.first.numtuples)
        if linear_search:
            block = self.__findblock(relation, key, eval_key)
            self.__insert(relation, block, tuple, get_key, eval_key)
        else:
            search_ans = relation.BPlusTree.search_for_node(key)
            index = search_ans[1]
            block = search_ans[0].children[index]
            return self.__insert(relation, block, tuple, get_key, eval_key)

    def __insert(self, relation, cursor, tuple, get_key, eval_key):
        if cursor.include(get_key(tuple), get_key):
            raise IndexError("key already exist!")
        cursor.insert(tuple, get_key, eval_key)
        if cursor.is_overflowblock_full():
            temp = []
            for i in cursor.tuples:
                if i is not None:
                    temp.append(i)
            for j in cursor.overflowblock:
                if j is not None:
                    temp.append(j)
            sorted_list = MainData.merge_sort(temp, get_key, eval_key)
            cursor.tuples = sorted_list
            # 将主block的元素和overfblock的元素进行merge，排好序都放到主block里面
            # print(cursor.item.tuples)
            #cursor.numtuples += self.overflow_size
            cursor.overflowblock = [None]*self.overflow_size
            if cursor.numtuples >= 0.75*self.blocksize:
                return self.__split(relation, cursor, get_key, eval_key)  # 对cursor这个节点进行分裂

    def delete(self, name, key, linear_search=1):
        if name not in self.tables:
            return None
        relation = self.name[name]
        eval_key = relation.eval_key
        get_key = relation.get_key
        #key = get_key(tuple)
        if linear_search:
            front, follow = self.__findblock_M(relation, key, eval_key)
            self.__delete(relation, front, follow, key, get_key, eval_key)
        else:
            search_ans = relation.BPlusTree.search_for_node(key)
            BNode = search_ans[0]
            # print("checking whether the BNode found is correct:", BNode.keys)
            index = search_ans[1]
            # follow = search_ans[0].children[search_ans[1]]
            # front = follow.pre
            return self.__delete_with_tree(relation, key, get_key, eval_key, BNode, index)

    def __delete_with_tree(self, relation, key, get_key, eval_key, node, index):
        if relation.numItems < 2:
            # params: relation, front, follow, key, get_key, eval_key
            return self.__delete(relation, None, node.children[index], key, get_key, eval_key)
        assert(relation.numItems >= 2)
        follow = node.children[index]
        front = follow.pre
        if front is None:
            minimal_key = follow.next.find_min_key(get_key, eval_key)
        else:
            minimal_key = follow.find_min_key(get_key, eval_key)
            # follow.show()
            # print("the minimal_key is: ", minimal_key)
        for i in range(len(follow.tuples)):
            if get_key(follow.tuples[i]) == key:
                follow.tuples[i] = None
                follow.maintain_bounds(get_key, eval_key)
                follow.numtuples -= 1
                if follow.numtuples <= 0.25*self.blocksize:
                    return [minimal_key, self.__merge(relation, front, follow, get_key, eval_key)]
                if key == minimal_key and index != 0:
                    assert(front is not None)
                    minimal_key = follow.find_min_key(get_key, eval_key)
                    assert(index != 0)
                    node.keys[index-1] = minimal_key
                return [None, None]
        for j in range(len(follow.overflowblock)):
            if get_key(follow.overflowblock[j]) == key:
                follow.overflowblock[j] = None
                follow.maintain_bounds(get_key, eval_key)
                follow.numtuples -= 1
                if follow.numtuples <= 0.25*self.blocksize:
                    return [minimal_key, self.__merge(relation, front, follow, get_key, eval_key)]
                if key == minimal_key and index != 0:
                    assert(front is not None)
                    minimal_key = follow.find_min_key(get_key, eval_key)
                    node.keys[index-1] = minimal_key
                return [None, None]
        raise Exception("No such key in this block")

    def __delete(self, relation, front, follow, key, get_key, eval_key):
        #print(follow.numtuples)
        for i in range(len(follow.tuples)):
            if get_key(follow.tuples[i]) == key:
                follow.tuples[i] = None
                follow.maintain_bounds(get_key, eval_key)
                # print(follow.minimum)
                # print(follow.maximum)
                follow.numtuples -= 1
                if follow.numtuples <= 0.25*self.blocksize and relation.numItems >= 2:
                    self.__merge(relation, front, follow, get_key, eval_key)
                return [None, None]
        for j in range(len(follow.overflowblock)):
            if get_key(follow.overflowblock[j]) == key:
                follow.overflowblock[j] = None
                follow.maintain_bounds(get_key, eval_key)
                follow.numtuples -= 1
                if follow.numtuples <= 0.25*self.blocksize and relation.numItems >= 2:
                    self.__merge(relation, front, follow, get_key, eval_key)
                return [None, None]
        raise Exception("No such key in this block")

    def __merge(self, relation, front, follow, get_key, eval_key):
        # print("#### MainData merge Blocks ####")
        new_key = None
        new_block = None
        if front == None:
            # delete follow.next
            assert(follow.next is not None)
            temp = follow.next
            tot = temp.tuples + temp.overflowblock
            follow.next = follow.next.next
            follow.next.pre = follow
            relation.numItems -= 1
            for item in tot:
                if item != None:
                    med = self.__insert(relation, follow, item, get_key, eval_key)
                    if med != None:
                        # new node occurs
                        follow = med[0]
                        new_block = med[0]
                        new_key = med[1]
            if new_block is None or new_key is None:
                return None
            return [new_block, new_key]
        else:
            # delete follow
            tot = follow.tuples + follow.overflowblock
            front.next = follow.next
            follow.next.pre = front
            relation.numItems -= 1
            for item in tot:
                if item != None:
                    med = self.__insert(relation, front, item, get_key, eval_key)
                    if med != None:
                        front = med[0]
                        new_block = med[0]
                        new_key = med[1]
            if new_block is None or new_key is None:
                return None
            return [new_block, new_key]

    def __split(self, relation, cursor, get_key, eval_key):
        # when split, the overflow block must be empty!!!
        follow = cursor.next
        cursor_tuples = []
        for i in cursor.tuples:
            if i is not None:
                cursor_tuples.append(i)
        cursor_size = len(cursor_tuples)
        newnode = MainData.DLinkedList.Block(self.blocksize, self.overflow_size)
        newnode.tuples = cursor.tuples[cursor_size // 2:]
        newnode.numtuples = cursor_size // 2
        newnode.maintain_bounds(get_key, eval_key)
        cursor.tuples = cursor.tuples[:cursor_size // 2]
        cursor.numtuples = cursor_size // 2
        cursor.maintain_bounds(get_key, eval_key)
        cursor.next = newnode
        newnode.pre = cursor
        newnode.next = follow
        relation.numItems += 1
        if follow != None:
            follow.pre = newnode
        return (newnode, get_key(newnode.tuples[0]))

    @staticmethod
    def __findblock(relation, key, eval_key):
        key_val = eval_key(key)
        prev = relation.first
        for block in relation:
            if block.numtuples == 0:
                return block
            # print(block.minimum)
            if block.minimum < key_val:
                prev = block
                continue
            else:
                break
        return prev

    @staticmethod
    def __findblock_M(relation, key, eval_key):
        key_val = eval_key(key)
        front = relation.first
        follow = front.next
        if follow == None:#只有一个block
            return (None, front)
        if key_val < follow.minimum:#要找的key出现在第一个block
            return (None, front)
        else:#要找的key出现在最后一个block
            while follow.next != None:
                if eval_key(key) < follow.next.minimum:
                    return (front, follow)
                follow = follow.next
                front = front.next
            return (front, follow)

    @staticmethod
    def merge_sort(lst, get_key, eval_key):
        if len(lst) <= 1:
            # 当列表元素只有一个的时候，直接返回
            return lst
        mid = len(lst) // 2
        left = lst[:mid]
        right = lst[mid:]

        left = MainData.merge_sort(left, get_key, eval_key)
        right = MainData.merge_sort(right, get_key, eval_key)
        # 递归的进行排序
        result = []
        while left and right:
            if eval_key(get_key(left[0])) <= eval_key(get_key(right[0])):
                result.append(left.pop(0))
            else:
                result.append(right.pop(0))
        if left:
            result += left
        if right:
            result += right
        return result

    def printall(self, name):
        schema = relation_schema[name]["schema"]
        relation = self.name[name]
        for cursor in relation:
            for item in cursor.tuples:
                if item is not None:
                    self.relation_print(item, schema)
            print("---")
            for item in cursor.overflowblock:
                if item is not None:
                    self.relation_print(item, schema)
            print("-----------")

    @staticmethod
    def relation_print(item, schema):
        assert(len(item) == len(schema))
        for i in range(len(item)):
            print(schema[i], end=": ")
            print(item[i], end="       ")
        print()
    
    def printTable(self, name):
        schema = relation_schema[name]["schema"]
        print(name)
        print("-"*40*len(schema))
        for attribute in schema:
            print("{:<40s}".format(attribute), end="") 
        print("\n"+"-"*40*len(schema))
        for block in self.name[name]:
            for tuple1 in block.tuples:
                if tuple1 != None:
                    for entry in tuple1:
                        print("{:<40s}".format(str(entry)), end="")
                    print("")                
            for tuple2 in block.overflowblock:
                if tuple2 != None:
                    for entry in tuple2:
                        print("{:<40s}".format(str(entry)), end="")
                    print("")
        print("-"*40*len(schema))
        print("")


if __name__ == "__main__":
    table_list = ["MOVIE"]
    a = MainData(table_list)
    a.insert("MOVIE", ('Titanic',1997,'USA',195,'romance'))
    a.insert("MOVIE", ('Shakespeare in Love',1998,'UK',122,'romance'))
    a.insert("MOVIE", ('The Cider House Rules',1999,'USA',125,'drama'))
    a.insert("MOVIE", ('Gandhi',1982,'India',188,'drama'))
    a.insert("MOVIE", ('American Beauty',1999,'USA',121,'drama'))
    a.insert("MOVIE", ('Affliction',1997,'USA',113,'drama'))
    a.insert("MOVIE", ('Life is Beautiful',1997,'Italy',118,'comedy'))
    a.insert("MOVIE", ('Boys Dont Cry',1999,'USA',118,'drama'))
    a.insert("MOVIE", ('Saving Private Ryan',1998,'USA',170,'action'))
    a.insert("MOVIE", ('The Birds',1963,'USA',119,'horror'))
    a.insert("MOVIE", ('The Matrix',1999,'USA',136,'action'))
    a.insert("MOVIE", ('Toy Story',1995,'USA',81,'animation'))
    a.insert("MOVIE", ('You have Got Mail',1998,'USA',119,'comedy'))
    a.insert("MOVIE", ('Proof of Life',2000,'USA',135,'drama'))
    a.insert("MOVIE", ('Hanging Up',2000,'USA',94,'comedy'))
    a.insert("MOVIE", ('The Price of Milk',2000,'New Zealand',87,'romance'))
    a.insert("MOVIE", ('The Footstep Man',1992,'New Zealand',89,'drama'))
    a.insert("MOVIE", ('Topless Women Talk About Their Lives',1997,'New Zealand',87,'drama'))
    a.insert("MOVIE", ('The Piano',1993,'New Zealand',121,'romance'))
    a.insert("MOVIE", ('Mad Max',1979,'Australia',88,'action'))
    a.insert("MOVIE", ('Strictly Ballroom',1992,'Australia',94,'comedy'))
    a.insert("MOVIE", ('My Mother Frank',2000,'Australia',95,'comedy'))
    a.insert("MOVIE", ('American Psycho',2000,'Canada',101,'horror'))
    a.insert("MOVIE", ('Scream 2',1997,'USA',116,'horror'))
    a.insert("MOVIE", ('Scream 3',2000,'USA',116,'horror'))

    print(a.find("MOVIE", ('Scream 3',2000)))
    a.delete("MOVIE", ('Scream 3',2000))
    a.delete("MOVIE", ('Titanic',1997))
    a.printall("MOVIE")
