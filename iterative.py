"""
AVL tree in imperative, iterative style.
"""

NODE    = 0

LEFT    = 0
ELEMENT = 1
HEIGHT  = 2
RIGHT   = 3


def make_node(element, left=None, right=None, height=1):
    """
    For preformance reasons, a node is encoded as a list.
    """
    return [ left, element, height, right ]


def height(node):
    """
    Return current height of node.
    """
    return 0 if node is None else node[HEIGHT]


def update_height(node):
    """
    Update node height field and return previous height.
    """
    rv = node[HEIGHT]

    node[HEIGHT] = 1 + max(height(node[LEFT]), height(node[RIGHT]))

    return rv


def balance_factor(node):
    """
    Return difference in height between right and left subtrees.
    """
    return height(node[RIGHT]) - height(node[LEFT])


def rotate_left(node):
    """
    Rotate node to the left.
    """
    root = node[RIGHT]
    node[RIGHT] = root[LEFT]
    root[LEFT] = node

    update_height(node)
    update_height(root)

    return root


def rotate_right(node):
    """
    Rotate node to the right.
    """
    root = node[LEFT]
    node[LEFT] = root[RIGHT]
    root[RIGHT] = node

    update_height(node)
    update_height(root)

    return root


def unwind(stack, node):
    """
    Unwind stack, balancing as we go.
    """
    while stack:
        parent, field = stack.pop()
        old = update_height(node)
        bf = balance_factor(node)

        if bf == 2:
            if balance_factor(node[RIGHT]) < 0:
                node[RIGHT] = rotate_right(node[RIGHT])

            parent[field] = rotate_left(node)

        elif bf == -2:
            if balance_factor(node[LEFT]) > 0:
                node[LEFT] = rotate_left(node[LEFT])

            parent[field] = rotate_right(node)

        elif node[HEIGHT] == old:
            return

        node = parent


class AVLTree:
    """
    Balanced binary tree.
    """
    def __init__(self, iterable=None):
        self.root = [ None ]

        for e in iterable or ():
            self.insert(e)


    def __iter__(self):
        def in_order(node):
            if node is not None:
                yield from in_order(node[LEFT])
                yield node[ELEMENT]
                yield from in_order(node[RIGHT])

        yield from in_order(self.root[NODE])


    @property
    def height(self):
        return height(self.root[NODE])


    def insert(self, element, replace=False):
        """
        Insert element into tree.
        Replaces any existing element if `replace` is True.
        Returns existing element, if any.
        """
        node = self.root[NODE]

        if node is None:
            self.root[NODE] = make_node(element)
            return

        stack = [ (self.root, NODE) ]

        while True:
            if node[ELEMENT] > element:
                if node[LEFT] is None:
                    node[LEFT] = make_node(element)
                    break

                stack.append((node, LEFT))
                node = node[LEFT]

            elif node[ELEMENT] < element:
                if node[RIGHT] is None:
                    node[RIGHT] = make_node(element)
                    break

                stack.append((node, RIGHT))
                node = node[RIGHT]

            else:
                rv = node[ELEMENT]

                if replace:
                    node[ELEMENT] = element

                return rv

        unwind(stack, node)


    def delete(self, element):
        """
        Delete element from tree.
        Returns existing element, if any.
        """
        node = self.root[NODE]
        stack = [ (self.root, NODE) ]

        while True:
            if not node:
                return

            elif node[ELEMENT] > element:
                stack.append((node, LEFT))
                node = node[LEFT]

            elif node[ELEMENT] < element:
                stack.append((node, RIGHT))
                node = node[RIGHT]

            else:
                break

        rv = node[ELEMENT]

        if node[LEFT] and node[RIGHT]:
            target = node
            stack.append((node, RIGHT))
            node = node[RIGHT]

            while node[LEFT]:
                stack.append((node, LEFT))
                node = node[LEFT]

            target[ELEMENT] = node[ELEMENT]
            node = node[RIGHT]

        else:
            node = node[LEFT] or node[RIGHT]

        parent, field = stack[-1]
        parent[field] = node

        if not node:
            node = parent
            stack.pop()

        unwind(stack, node)

        return rv


    def to_tuple(self):
        """
        Return tree as tuples.
        """
        def tpl(n):
            if n:
                return (tpl(n[LEFT]), n[ELEMENT], n[HEIGHT], tpl(n[RIGHT]))

        return tpl(self.root[NODE])
