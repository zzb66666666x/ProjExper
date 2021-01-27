class Queue:
    class __Node:
        def __init__(self, val):
            self.val = val
            self.next = None

    def __init__(self, content=[]):
        self.head = None
        self.end = None
        for i in content:
            self.enqueue(i)

    def enqueue(self, val):
        node = self.__Node(val)
        if self.end is None:
            assert (self.head is None)
            self.head = self.end = node
        else:
            self.end.next = node
            self.end = node

    def dequeue(self):
        if self.head is None:
            return None
        node = self.head
        self.head = node.next
        if self.head is None:
            self.end = None
        return node.val

    def is_empty(self):
        if self.head is None:
            assert (self.end is None)
            return True
        return False

    def show(self):
        temp = self.head
        while temp is not None:
            print(temp.val)
            temp = temp.next