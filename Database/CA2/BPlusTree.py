# code of BPlus tree
from math import ceil
from schema import *

disk_layer = True
upper_layer = False

class BptNode:
    def __init__(self, order, layer, first_block=None):
        self.layer = layer
        self.parent = None
        self.order = order
        self.keys, self.children = [], []
        if first_block is not None:
            self.children.append(first_block)
        self.max = self.order - 1
        self.min = ceil(self.order/2) - 1

        # whether the node is full
    def isFull(self):
        return len(self.keys) > self.max

    def shouldMerge(self):
        return len(self.keys) < self.min

    def isRich(self):
        return len(self.keys) > self.min

class BPlusTree:
    def __init__(self, table_name, first_block, order = 5):
        self.table = table_name
        self.order = order
        # traverse as Tree
        self.root = BptNode(order, disk_layer, first_block)
        # traverse leaves as LinkedList
        self.get_key = get_key_table[table_name]
        self.eval_key = eval_key_string

    def insert(self, key, data_ptr):

        def split(oldNode):
            mid = (self.order) // 2
            # print(mid)
            if oldNode.layer is disk_layer:
                newNode = BptNode(self.order, disk_layer)
                # print("checking newnode keys:", oldNode.keys[mid:])
                newNode.keys, newNode.children = oldNode.keys[mid+1:], oldNode.children[mid+1:]
                newNode.parent = oldNode.parent
            else:
                newNode = BptNode(self.order, upper_layer)
                newNode.keys, newNode.children = oldNode.keys[mid+1:], oldNode.children[mid+1:]
                newNode.parent = oldNode.parent
                for child in newNode.children:
                    child.parent = newNode
            if oldNode.parent == None:
                newRoot = BptNode(self.order, upper_layer)
                newRoot.keys, newRoot.children = [oldNode.keys[mid]], [oldNode, newNode]
                oldNode.parent = newNode.parent = newRoot
                self.root = newRoot
            else:
                # now suppose the c is the oldNode and this "c" is full which has been separated
                #   1 2 3 4
                #  / \ \ \ \
                # a   b c d e
                # out target is:
                # split the c to be: c1 * c2
                #   1  2  *  3  4
                #  / \  \  \  \  \
                # a   b c1  c2 d  e
                # the old node here is c
                # so the i should be 2 because c was the third in the children list
                # then * belongs to this position in key list, so we get [1 2 * 3 4]
                # that's why the forth position (with index 3) in the parent's children list belongs to c2
                i = oldNode.parent.children.index(oldNode)
                oldNode.parent.keys.insert(i, oldNode.keys[mid])
                oldNode.parent.children.insert(i+1, newNode)
                if oldNode.parent.isFull():
                    # this is possible because the parent may contain 3 elements before
                    # after adding a new thing to it, we get a new full parent list: triggering new split
                    split(oldNode.parent)
            # the rest of the oldNode is key: [1] and children[a,b]
            oldNode.keys = oldNode.keys[:mid]
            oldNode.children = oldNode.children[:mid+1]
            # the split of oldNode's parent will maintain the "parent" attribute of its children, so this oldNode parent is correct
            return oldNode.parent

        def __insert(node):
            if node.layer is upper_layer:
                if node.isFull():
                    # facing a full node, then split it and insert to its parent
                    # inserting to returned parent node will help us figure out where to insert
                    # which means that you don't have to determine whether the newly inserted thing should be in the node or node's parent
                    # the work of determining where to insert belongs to the function __bisect()
                    # the __bisect is just a binary search
                    __insert(split(node))
                else:
                    index = BPlusTree.__bisect(node.keys, key)
                    __insert(node.children[index])
            else:
                index = BPlusTree.__bisect(node.keys, key)
                node.keys.insert(index, key)
                node.children.insert(index+1, data_ptr)
                if node.isFull():
                    # print("full!!!")
                    # print("checking why the node is full:", node.keys)
                    split(node)
        __insert(self.root)

    def search(self, key):
        # supporting range queries
        node = self.root
        block = self.__search(node, key, 1)
        return block.find(key, self.get_key, self.eval_key)

    def search_for_node(self, key):
        return self.__search(self.root, key, 0)

    def __search(self, node, key, flag):
        if node.layer is disk_layer:
            # print("########")
            # print("disk layer")
            # print(key)
            # print(node.keys)
            index = BPlusTree.__bisect(node.keys, key)
            # print(len(node.children))
            # print(index)
            # print(node.children[index].tuples)
            # print("#######")
            if flag:
                return node.children[index]
            else:
                return (node, index)
        else:
            index = BPlusTree.__bisect(node.keys, key)
            return self.__search(node.children[index], key, flag)
                
    def delete(self, key):
        self.__delete(self.root, key)

    def __delete(self, node, key):
        # check layer
        # if not disk_layer: swap key and delete children first
        # if disk_layer: delete it and remove the right child; then check the number of elements left and recursion upward4
        # call merge_upward
        index = BPlusTree.__bisect(node.keys, key)
        if node.layer != disk_layer:
            # print("checking the index from bisect:", index)
            # print("checking the node.keys in __delete: ",node.keys)
            if key in node.keys:
                assert(index >= 1)
                node.keys[index-1] = node.children[index].keys[0]
                self.__delete_children_first(node.children[index], key)
            else:
                self.__delete(node.children[index], key)
        else:
            assert(index >= 1)
            # print("what is in the node.keys: ",node.keys[index-1])
            # print("what key to delete",key)
            # print("######")
            # print("show the node.children[index-1]")
            node.children[index-1].show()
            # print("show the node.children[index]")
            node.children[index].show()
            # print("#####")
            node.keys.pop(index-1)
            node.children.pop(index)
            self.__merge_upward(node)


    def __delete_children_first(self, node, key):
        # check layer
        # if not disk_layer, swap key again and recursively call itself
        # if finally, the node is at disk_layer, remove the key[0] as well as its children[0]
        # check the number of elements left and recursion upward
        # call merge_upward
        if node.layer != disk_layer:
            index = BPlusTree.__bisect(node.keys, key)
            node.keys[index] = node.children[index].keys[0]
            self.__delete_children_first(node.children[index], key)
        else:
            node.keys.pop(0)
            node.children.pop(0)
            self.__merge_upward(node)


    def __merge_upward(self, node):
        # find the node's left sibling and also right sibling, find one to use
        # if left or right sibling don't have sufficient keys, then directly get one from parent and merge
        if node.parent is None:
            if node.layer is disk_layer:
                if len(node.keys) == 0:
                    # the whole B+ tree will be deleted (but save one pointer)
                    assert(len(node.children)==1)
            else:
                if len(node.keys) == 0:
                    assert(len(node.children)==1)
                    # change for a new root
                    self.root = node.children[0]
                    node.children[0].parent = None
        else:
            if not node.shouldMerge():
                return
            # check left siblings and right siblings
            # the index of my self
            my_index = node.parent.children.index(node)
            # print("checking my index here: ", my_index)
            if my_index == len(node.parent.children)-1:
                # node is the last children of parent -> no right sibling
                left_sib = node.parent.children[my_index-1]
                right_sib = None
            elif my_index == 0:
                # the node is the first children of parent -> no left sibling
                left_sib = None
                right_sib = node.parent.children[my_index+1]
            else:
                left_sib = node.parent.children[my_index-1]
                right_sib = node.parent.children[my_index+1]
            if left_sib is not None and left_sib.isRich():
                node.keys.insert(0, node.parent.keys[my_index-1])
                node.children.insert(0, left_sib.children[-1])
                if node.layer is not disk_layer:
                    left_sib.children[-1].parent = node
                node.parent.keys[my_index-1] = left_sib.keys[-1]
                left_sib.keys.pop(-1)
                left_sib.children.pop(-1)
            elif right_sib is not None and right_sib.isRich():
                node.keys.append(node.parent.keys[my_index])
                node.children.append(right_sib.children[0])
                if node.layer is not disk_layer:
                    right_sib.children[0].parent = node
                node.parent.keys[my_index] = right_sib.keys[0]
                right_sib.keys.pop(0)
                right_sib.children.pop(0)
            else:
                # merge things
                if left_sib is not None:
                    # merge to the left
                    separator_key = node.parent.keys[my_index-1]
                    # print("checking sep key:", separator_key)
                    left_sib.keys.append(separator_key)
                    left_sib.keys += node.keys
                    left_sib.children += node.children
                    node.parent.keys.pop(my_index-1)
                    node.parent.children.pop(my_index)
                    # print("checking node.parent: ", node.parent.keys)
                    self.__merge_upward(node.parent)
                else:
                    assert(right_sib is not None)
                    separator_key = node.parent.keys[my_index]
                    node.keys.append(separator_key)
                    node.keys += right_sib.keys
                    node.children += right_sib.children
                    node.parent.keys.pop(my_index)
                    node.parent.children.pop(my_index+1)
                    self.__merge_upward(node.parent)

    @staticmethod
    def __bisect(a, x, low=0, high=None):
        #   1 2 3 4
        #  / \ \ \ \
        # a   b c d e
        # now I want to insert 4.5 which is larger than 4, I need e then
        # at first, the mid index is 2, corresponding value is 3 -> go to right
        # then I search between index 3 and 4, corresponding value range is 4 and None
        # mid should be 3, a[3] = 4, then low = 4, high = 4 -> out of the loop
        # return the 4 as the index of children because children[4] = e

        # now I want to insert 3.5, I need child d
        # at first, the mid index is 2, corresponding value is 3 -> go to right
        # then I search between index 3 and 4, corresponding value range is 4 and None
        # mid should be 3, a[3] = 4, a[3]>3.5, so we get low = high = mid = 3 -> out of loop
        # return the 3 as the index of children because children[3] = d
        if high is None:
            high = len(a)
        while low < high:
            mid = (low + high) // 2
            # print(x)
            # print(a[mid])
            if x >= a[mid]:
                low = mid + 1
            else:
                high = mid
        return low



