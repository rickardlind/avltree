"""
AVL tree in object-oriented, recursive style.
"""

class AVLTree:
    class Node:
        def __init__(self, element=None, left=None, right=None, height=0):
            self.element = element
            self.left = left
            self.right = right
            self.height = height


        def __bool__(self):
            return self != AVLTree.NONE


        def __iter__(self):
            if self.left:
                yield from self.left

            if self:
                yield self.element

            if self.right:
                yield from self.right


        def insert(self, element):
            if not self:
                return AVLTree.Node(element, AVLTree.NONE, AVLTree.NONE, 1)

            elif self.element > element:
                self.left = self.left.insert(element)

            elif self.element < element:
                self.right = self.right.insert(element)

            else:
                return self

            self.updateHeight()

            return self.balance()


        def delete(self, element):
            node = self

            if not self:
                return self

            elif self.element > element:
                self.left = self.left.delete(element)

            elif self.element < element:
                self.right = self.right.delete(element)

            elif not (self.left and self.right):
                return self.left or self.right

            else:
                node, right = self.right.leftMost()
                node.left = self.left
                node.right = right

            node.updateHeight()

            return node.balance()


        def leftMost(self):
            if not self.left:
                return self, self.right

            node, self.left = self.left.leftMost()

            self.updateHeight()

            return node, self.balance()


        def updateHeight(self):
            self.height = 1 + max(self.left.height, self.right.height)


        def balanceFactor(self):
            return self.right.height - self.left.height


        def balance(self):
            bf = self.balanceFactor()

            if bf == 2:
                if self.right.balanceFactor() < 0:
                    self.right = self.right.rotateRight()

                return self.rotateLeft()

            elif bf == -2:
                if self.left.balanceFactor() > 0:
                    self.left = self.left.rotateLeft()

                return self.rotateRight()

            return self


        def rotateLeft(self):
            node = self.right
            self.right = node.left
            node.left = self

            self.updateHeight()
            node.updateHeight()

            return node


        def rotateRight(self):
            node = self.left
            self.left = node.right
            node.right = self

            self.updateHeight()
            node.updateHeight()

            return node


    NONE = Node()


    def __init__(self, iterable=None):
        self.root = self.NONE

        for e in iterable or ():
            self.insert(e)


    def __iter__(self):
        yield from self.root


    @property
    def height(self):
        return self.root.height


    def insert(self, element):
        self.root = self.root.insert(element)


    def delete(self, element):
        self.root = self.root.delete(element)


    def toTuple(self):
        def tpl(node):
            if node != self.NONE:
                return (tpl(node.left), node.element, node.height, tpl(node.right))

        return tpl(self.root)
