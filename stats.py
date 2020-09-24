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


def average(v: list, cnt: int, scale: float) -> float:
    return sum(map(lambda x: (x * scale) / cnt, v)) / len(v)


def table(param, scale, unit, test, operation, types, result):
    """
    Print average time of an operation.
    """
    lines = [ [ 'height', 'count', *types]  ]

    for d in result:
        line = [ d['height'], d['count'] ]

        for t in types:
            line.append(average(d[t], d['count'], scale))

        lines.append(line)

    print(f'{test.title()} - {operation} performance ({unit}s):')

    for line in lines:
        print('\t'.join(map(display, line)))


def graph(param, scale, unit, test, operation, types, result):
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
            y.append(average(d[t], d['count'], scale))

        plt.plot(x, y, label=t)

    plt.title(f'{test.title()} performance')
    plt.xlabel('Tree height')
    plt.ylabel(f'Average {operation} time ({unit}s)')
    plt.legend()

    plt.savefig(param.output, type='svg')


UNITS = {
    's':  (1.0,            ''),
    'ms': (1000.0,         'm'),
    'us': (1000_000.0,     '\u00B5'),
    'ns': (1000_000_000.0, 'n')
}


if __name__ == '__main__':
    ap = argparse.ArgumentParser('Display tree')

    ap.add_argument('--type', choices=('table','graph'), default='table',
                    help='Output type (default: table)')

    ap.add_argument('--result', metavar='PATH', default='result.json',
                    help='Input file (default: result.json)')

    ap.add_argument('--output', metavar='PATH',
                    help='output file')

    ap.add_argument('--unit', choices=UNITS, default='us',
                    help='Time unit (default: microseconds)')

    param = ap.parse_args()
    scale, unit = UNITS[param.unit]

    with open(param.result) as fp:
        d = json.load(fp)

    if param.type == 'table':
        table(param, scale, unit, **d)

    else:
        graph(param, scale, unit, **d)
