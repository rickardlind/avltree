"""
AVL tree in functional style.
"""

def left(t):
    return t[0]


def element(t):
    return t[1]


def height(t):
    return t[2] if t else 0


def right(t):
    return t[3]


def node(l, e, r, h=None):
    if h is None:
        h = 1 + max(height(l), height(r))

    return (l, e, h, r)


def balanceFactor(t):
    return height(right(t)) - height(left(t))


def rotateLeft(t):
    r = right(t)
    l = node(left(t), element(t), left(r))

    return node(l, element(r), right(r))


def rotateRight(t):
    l = left(t)
    r = node(right(l), element(t), right(t))

    return node(left(l), element(l), r)


def balance(t):
    bf = balanceFactor(t)

    if bf == 2:
        r = right(t)

        if balanceFactor(r) < 0:
            t = node(left(t), element(t), rotateRight(r))

        return rotateLeft(t)

    if bf == -2:
        l = left(t)

        if balanceFactor(l) > 0:
            t = node(rotateLeft(l), element(t), right(t))

        return rotateRight(t)

    return t


def insert(t, e):
    if not t:
        return node(None, e, None, 1)

    p = element(t)

    if p > e:
        return balance(node(insert(left(t), e), p, right(t)))

    if p < e:
        return balance(node(left(t), p, insert(right(t), e)))

    return t


def leftmost(t):
    if not left(t):
        return element(t), right(t)

    e, l = leftmost(left(t))

    return e, balance(node(l, element(t), right(t)))


def delete(t, e):
    if not t:
        return None

    p, l, r = element(t), left(t), right(t)

    if p > e:
        return balance(node(delete(l, e), p, r))

    if p < e:
        return balance(node(l, p, delete(r, e)))

    if not (l and r):
        return l or r

    p, r = leftmost(r)

    return balance(node(l, p, r))


def avltree(iterable=None, t=None):
    for e in iterable or ():
        t = insert(t, e)

    return t


def inorder(t):
    if t:
        yield from inorder(left(t))
        yield element(t)
        yield from inorder(right(t))
