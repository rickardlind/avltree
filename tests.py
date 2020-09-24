#!/usr/bin/env python3

import argparse
import bisect
import inspect
import json
import logging
import os
import random
import sys
import time
import unittest

sys.path.append(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))

import recursive
import functional
import iterative
import cavltree


class CorrectnessTest(unittest.TestCase):
    INSERT = [
        ('M', (None, 'M', 1, None)),
        ('N', (None, 'M', 2, (None, 'N', 1, None))),
        # Left rotation
        ('O', ((None, 'M', 1, None), 'N', 2, (None, 'O', 1, None))),
        ('L', (((None, 'L', 1, None), 'M', 2, None), 'N', 3, (None, 'O', 1, None))),
        # Right rotation
        ('K', (((None, 'K', 1, None), 'L', 2, (None, 'M', 1, None)), 'N', 3, (None, 'O', 1, None))),
        ('Q', (((None, 'K', 1, None), 'L', 2, (None, 'M', 1, None)), 'N', 3, (None, 'O', 2, (None, 'Q', 1, None)))),
        # Right-Left rotation
        ('P', (((None, 'K', 1, None), 'L', 2, (None, 'M', 1, None)), 'N', 3, ((None, 'O', 1, None), 'P', 2, (None, 'Q', 1, None)))),
        ('H', ((((None, 'H', 1, None), 'K', 2, None), 'L', 3, (None, 'M', 1, None)), 'N', 4, ((None, 'O', 1, None), 'P', 2, (None, 'Q', 1, None)))),
        # Left-Right rotation
        ('I', ((((None, 'H', 1, None), 'I', 2, (None, 'K', 1, None)), 'L', 3, (None, 'M', 1, None)), 'N', 4, ((None, 'O', 1, None), 'P', 2, (None, 'Q', 1, None)))),
        # Right rotation with children
        ('A', ((((None, 'A', 1, None), 'H', 2, None), 'I', 3, ((None, 'K', 1, None), 'L', 2, (None, 'M', 1, None))), 'N', 4, ((None, 'O', 1, None), 'P', 2, (None, 'Q', 1, None)))),
    ]

    DELETE = [
        # No children
        ('A', (((None, 'H', 1, None), 'I', 3, ((None, 'K', 1, None), 'L', 2, (None, 'M', 1, None))), 'N', 4, ((None, 'O', 1, None), 'P', 2, (None, 'Q', 1, None)))),
        # One child
        ('H', (((None, 'A', 1, None), 'I', 3, ((None, 'K', 1, None), 'L', 2, (None, 'M', 1, None))), 'N', 4, ((None, 'O', 1, None), 'P', 2, (None, 'Q', 1, None)))),
        # Two children
        ('I', ((((None, 'A', 1, None), 'H', 2, None), 'K', 3, (None, 'L', 2, (None, 'M', 1, None))), 'N', 4, ((None, 'O', 1, None), 'P', 2, (None, 'Q', 1, None)))),
    ]

    def testInsert(self):
        f = None
        r = recursive.AVLTree()
        i = iterative.AVLTree()
        c = cavltree.AVLTree()

        for e, expected in self.INSERT:
            f = functional.insert(f, e)
            self.assertEqual(f, expected)

            r.insert(e)
            self.assertEqual(r.toTuple(), expected)

            i.insert(e)
            self.assertEqual(i.to_tuple(), expected)

            c.insert(e)
            self.assertEqual(c.to_tuple(), expected)


    def testDelete(self):
        for e, expected in self.DELETE:
            f = functional.avltree(t[0] for t in self.INSERT)
            self.assertEqual(f, self.INSERT[-1][1])

            f = functional.delete(f, e)
            self.assertEqual(f, expected)

            r = recursive.AVLTree(t[0] for t in self.INSERT)
            self.assertEqual(r.toTuple(), self.INSERT[-1][1])

            r.delete(e)
            self.assertEqual(r.toTuple(), expected)

            i = iterative.AVLTree(t[0] for t in self.INSERT)
            self.assertEqual(i.to_tuple(), self.INSERT[-1][1])

            i.delete(e)
            self.assertEqual(i.to_tuple(), expected)

            c = cavltree.AVLTree(t[0] for t in self.INSERT)
            self.assertEqual(c.to_tuple(), self.INSERT[-1][1])

            c.delete(e)
            self.assertEqual(c.to_tuple(), expected)


UINT64_MAX = 2 ** 64 - 1


def randints(cnt: int):
    while cnt:
        yield random.randint(0, UINT64_MAX)
        cnt -= 1


def choices(v, cnt: int):
    s = set()

    while cnt:
        e = random.choice(v)

        if not e in s:
            s.add(e)
            cnt -= 1
            yield e


def insort(v: list, iterable):
    for e in iterable:
        i = bisect.bisect_left(v, e)

        if i < len(v) and v[i] == e:
            logging.debug('insort: duplicate element: %s', str(e))
            continue

        v.insert(i, e)


def rexp(s: str):
    """
    Parse range expression.
    """
    if ',' in s:
        for e in s.split(','):
            yield from rexp(e)

    elif '-' in s:
        l, h = s.split('-', maxsplit=1)
        yield from range(int(l), int(h) + 1)

    else:
        yield int(s)


def capacity(height: int) -> int:
    """
    Max number of nodes in a tree of given height.
    """
    assert height >= 0
    return (2 ** height) - 1


def layer(height: int) -> int:
    """
    Max number of nodes in the lowest layer of a tree of given height.
    """
    assert height > 0
    return 2 ** (height - 1)


class Stopwatch:
    def __enter__(self):
        self.start = time.perf_counter()
        self.lap = self.start
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.total = self.elapsed(self.start)


    def elapsed(self, since: float=None) -> float:
        if since is None:
            since = self.lap

        now = time.perf_counter()
        lap = now - since

        self.lap = now

        return lap


class PerformanceTest(unittest.TestCase):
    HEIGHTS = list(rexp(os.environ.get('HEIGHTS', '5-20')))
    TRIES   = int(os.environ.get('TRIES', 5))
    OUTPUT  = os.environ.get('OUTPUT', '.')
    TYPES   = [ 'list', 'functional', 'recursive', 'iterative', 'extension' ]


    def setUp(self):
        random.seed(os.environ.get('SEED'))


    def testFill(self):
        """
        Measure the time it takes to fill a tree to a given height.
        """
        result = []
        output = {
            'test': 'fill',
            'operation': 'insert',
            'types': self.TYPES,
            'result': result
        }

        for height in self.HEIGHTS:
            count = capacity(height)

            d = {
                'height': height,
                'count': count
            }

            for k in output['types']:
                d[k] = []

            result.append(d)

            for n in range(1, self.TRIES + 1):
                logging.debug('height: %d, count: %d, try: %d', height, count, n)

                source = list(randints(count))

                # Built-in list
                v = []

                with Stopwatch() as sw:
                    insort(v, source)

                d['list'].append(sw.total)

                # Functional
                with Stopwatch() as sw:
                    ftree = functional.avltree(source)

                d['functional'].append(sw.total)

                # Recursive
                with Stopwatch() as sw:
                    rtree = recursive.AVLTree(source)

                d['recursive'].append(sw.total)

                # Iterative
                with Stopwatch() as sw:
                    itree = iterative.AVLTree(source)

                d['iterative'].append(sw.total)

                # Extension
                with Stopwatch() as sw:
                    etree = cavltree.AVLTree(source)

                d['extension'].append(sw.total)

                # Check correctness
                f = list(functional.inorder(ftree))
                r = list(rtree)
                i = list(itree)
                e = list(etree)

                source = sorted(set(source))

                self.assertEqual(v, source)
                self.assertEqual(f, source)
                self.assertEqual(r, source)
                self.assertEqual(i, source)
                self.assertEqual(e, source)

        with open(os.path.join(self.OUTPUT, 'fill.json'), 'w') as fp:
            json.dump(output, fp, indent=4)


    def testInsert(self):
        """
        First fill a tree to a given height such that the bottom
        layer is half full, then measure the time it takes to
        insert another quarter.
        """
        result = []
        output = {
            'test': 'insert',
            'operation': 'insert',
            'types': self.TYPES,
            'result': result
        }

        for height in self.HEIGHTS:
            bottom = layer(height)
            initial = capacity(height - 1) + (bottom // 2)
            count = bottom // 4

            d = {
                'height': height,
                'count': count
            }

            for k in output['types']:
                d[k] = []

            result.append(d)

            for n in range(1, self.TRIES + 1):
                logging.debug('height: %d, count: %d, try: %d', height, count, n)

                source = list(randints(initial))
                extend = list(randints(count))

                # Built-in list
                v = []
                insort(v, source)

                with Stopwatch() as sw:
                    insort(v, extend)

                d['list'].append(sw.total)

                # Functional
                ftree = functional.avltree(source)

                with Stopwatch() as sw:
                    ftree = functional.avltree(extend, ftree)

                d['functional'].append(sw.total)

                # Recursive
                rtree = recursive.AVLTree(source)

                with Stopwatch() as sw:
                    for e in extend:
                        rtree.insert(e)

                d['recursive'].append(sw.total)

                # Iterative
                itree = iterative.AVLTree(source)

                with Stopwatch() as sw:
                    for e in extend:
                        itree.insert(e)

                d['iterative'].append(sw.total)

                # Extension
                etree = cavltree.AVLTree(source)

                with Stopwatch() as sw:
                    for e in extend:
                        etree.insert(e)

                d['extension'].append(sw.total)

                # Check correctness
                f = list(functional.inorder(ftree))
                r = list(rtree)
                i = list(itree)
                e = list(etree)

                source = sorted(set(source + extend))

                self.assertEqual(v, source)
                self.assertEqual(f, source)
                self.assertEqual(r, source)
                self.assertEqual(i, source)
                self.assertEqual(e, source)

        with open(os.path.join(self.OUTPUT, 'insert.json'), 'w') as fp:
            json.dump(output, fp, indent=4)


    def testDelete(self):
        """
        First fill a tree to a given height such that the bottom
        layer is half full, then measure the time it takes to
        remove random elements until it is quarter full.
        """
        result = []
        output = {
            'test': 'delete',
            'operation': 'delete',
            'types': self.TYPES,
            'result': result
        }

        for height in self.HEIGHTS:
            bottom = layer(height)
            initial = capacity(height - 1) + (bottom // 2)
            count = bottom // 4

            d = {
                'height': height,
                'count': count
            }

            for k in output['types']:
                d[k] = []

            result.append(d)

            for n in range(1, self.TRIES + 1):
                logging.debug('height: %d, count: %d, try: %d', height, count, n)

                source = list(randints(initial))
                remove = list(choices(source, count))

                # Built-in list
                v = []
                insort(v, source)

                with Stopwatch() as sw:
                    for e in remove:
                        i = bisect.bisect_left(v, e)
                        del v[i]

                d['list'].append(sw.total)

                # Functional
                ftree = functional.avltree(source)

                with Stopwatch() as sw:
                    for e in remove:
                        ftree = functional.delete(ftree, e)

                d['functional'].append(sw.total)

                # Recursive
                rtree = recursive.AVLTree(source)

                with Stopwatch() as sw:
                    for e in remove:
                        rtree.delete(e)

                d['recursive'].append(sw.total)

                # Iterative
                itree = iterative.AVLTree(source)

                with Stopwatch() as sw:
                    for e in remove:
                        itree.delete(e)

                d['iterative'].append(sw.total)

                # Extension
                ctree = cavltree.AVLTree(source)

                with Stopwatch() as sw:
                    for e in remove:
                        ctree.delete(e)

                d['extension'].append(sw.total)

                # Check correctness
                f = list(functional.inorder(ftree))
                r = list(rtree)
                i = list(itree)
                c = list(ctree)

                source.sort()

                for e in remove:
                    source.remove(e)

                self.assertEqual(v, source)
                self.assertEqual(f, source)
                self.assertEqual(r, source)
                self.assertEqual(i, source)
                self.assertEqual(c, source)

        with open(os.path.join(self.OUTPUT, 'delete.json'), 'w') as fp:
            json.dump(output, fp, indent=4)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s %(levelname)s: %(message)s',
                        level='DEBUG', stream=sys.stderr)
    unittest.main()
