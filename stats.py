#!/usr/bin/env python3

import argparse
import json


def display(field):
    W = 8
    D = 7

    if isinstance(field, str):
        return '%*s' % (-W, field)

    if isinstance(field, float):
        return '%*.*f' % (W, D, field)

    if isinstance(field, int):
        return '%*d' % (W, field)

    field = '-' if field is None else str(field)

    return '%*s' % (W, field)


def stats(v, cnt, tries):
    tot = sum(v) / tries
    avg = sum(map(lambda x: x / cnt, v)) / tries

    return tot, avg


def average(v: list, cnt: int, scale: float) -> float:
    return sum(map(lambda x: (x * scale) / cnt, v)) / len(v)


def table(param, test, operation, types, result):
    """
    Print average time of an operation.
    """
    lines = [ [ 'height', 'count', *types]  ]

    for d in result:
        line = [ d['height'], d['count'] ]

        for t in types:
            line.append(average(d[t], d['count'], param.scale))

        lines.append(line)

    print(f'{test.title()} - {operation} performance:')

    for line in lines:
        print('\t'.join(map(display, line)))


def graph(param, test, operation, types, result):
    """
    Use matplotlib to create graph as a SVG file.
    """
    import matplotlib
    matplotlib.use('cairo')

    import matplotlib.pyplot as plt

    for t in types:
        x, y = [], []

        for d in result:
            x.append(d['height'])
            y.append(average(d[t], d['count'], param.scale))

        plt.plot(x, y, label=t)

    plt.title(f'{test.title()} performance')
    plt.xlabel('Tree height')
    plt.ylabel(f'Average {operation} time (\u00B5s)')
    plt.legend()

    plt.savefig(f'{test}.svg', type='svg')


if __name__ == '__main__':
    ap = argparse.ArgumentParser('Display tree')

    ap.add_argument('--type', choices=('table','graph'), default='table',
                    help='Output type (default: table)')

    ap.add_argument('--result', metavar='PATH', default='result.json',
                    help='Input file (default: result.json)')

    ap.add_argument('--scale', metavar='FACTOR', type=float, default=1000_000.0,
                    help='Scale factor (default: microseconds)')

    param = ap.parse_args()

    with open(param.result) as fp:
        d = json.load(fp)

    if param.type == 'table':
        table(param, **d)

    else:
        graph(param, **d)
