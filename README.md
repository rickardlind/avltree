# AVL trees in Python (and C)
An [AVL tree]}(https://en.wikipedia.org/wiki/AVL_tree) is a self-balancing binary tree. This project explores three pure Python implementations and one Python module in C.

# TL;DR
A pure Python implementation is slower than using the built-in list type and the standard library `bisect` module unless you have a *lot* of elements.

# Functional
The simplest implementation is the [functional](functional.py). It uses the built-in `tuple` type for tree nodes and recursive functions for `insert` and `delete`. Each operation needs to replace all the nodes in the path to the root (even if they have not changed), which is both inefficient and inconvenient.

# Recursive
The [recursive](recursive.py) implementation tries to improve on the functional by using a mode object-oriented style. Nodes are Python objects, which are mutable, and there is an enclosing tree object which tracks the current root.

# Iterative
The [iterative](iterative.py) implementation attempts some basic optimisations. Nodes are of the built-in `list` type, which are mutable and faster to create that Python objects. The `insert` and `delete` functions use iterative algorithms which allow them to short-circuit.
