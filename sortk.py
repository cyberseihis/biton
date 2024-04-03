from numpy import argsort, log2
from operator import sub
from random import shuffle, choice
from itertools import groupby
from math import inf
from typing import Dict
from inhibitor import comp
from pylse import Wire
import pylse


def alt(n: int, x: int) -> list[bool]:
    return [(i // x) % 2 == 1 for i in range(n)]


def sarrows(n: int, stride: int, xstride: int) -> list[tuple[int, int]]:
    s = stride * 2
    steps = n // s
    arr = [(i, i + stride) for i in range(stride)]
    arrn = [(j, i) for i, j in arr]
    alts = alt(steps, xstride)
    sarr = [
        (x * s + i, x * s + j)
        for x in range(steps)
        for i, j in (arrn if alts[x] else arr)
    ]
    return sarr


def lnums(x: int) -> list[tuple[int, int]]:
    xs = [2**i for i in range(x)]
    return list(zip(xs[::-1], xs))


def carrows(n: int) -> list[tuple[int, int, int]]:
    lgn = int(log2(n))
    layers = sum((lnums(i) for i in range(1, lgn + 1)), [])
    return [(n, x, y) for x, y in layers]


def layers(n: int) -> list[list[tuple[int, int]]]:
    return [sarrows(*x) for x in carrows(n)]


def mklayer(
    lcons: list[tuple[int, int]],
    inplist: list[Wire],
    retin: list[Wire],
    retback: list[Wire],
) -> list[Wire]:
    o = [Wire() for _ in inplist]
    for i, j in lcons:
        o[i], o[j] = comp(
            inplist[i], inplist[j], retin[i], retin[j], retback[i], retback[j]
        )
    return o


def sortk(
    n: int, inplist: list[Wire], retlist: list[Wire]
) -> tuple[list[Wire], list[Wire]]:
    las = layers(n)
    r = [[Wire() for _ in range(n)] for _ in las] + [retlist]
    f = [inplist]
    for i, layer in enumerate(las):
        f.append(mklayer(layer, f[-1], r[i + 1], r[i]))
    bsorted = f[-1]
    btopk = r[0]
    return bsorted, btopk


def demo_sortk(ils: list[float], rls: list[bool], plot: bool = True):
    pylse.working_circuit().reset()
    n = len(ils)
    inplist = [pylse.inp_at(x, name=f"x{i}") for i, x in enumerate(ils)]
    retlist = [pylse.inp_at(*([200] * x), name=f"r{i}") for i, x in enumerate(rls)]
    o, ro = sortk(n, inplist, retlist)
    for i, x in enumerate(o):
        pylse.inspect(x, f"o{i}")
    for i, x in enumerate(ro):
        pylse.inspect(x, f"ro{i}")
    sim = pylse.Simulation()
    events = sim.simulate()
    towatch = ["x", "r", "o", "ro"]
    watchers = [[f"{x}{i}" for i in range(n)] for x in towatch]
    watch_wires = sum(watchers, [])
    if plot:
        sim.plot(wires_to_display=watch_wires)
    ex, er, eo, ero = events_io(events, towatch)
    check_out(ex, er, eo, ero)
    return events


def quick_sort(n, plot: bool = True):
    rls = [choice([True, False]) for _ in range(n)]
    # ils: list[float] = list(range(10, (n + 1) * 10, 10))
    # shuffle(ils)
    ils: list[float] = [choice(range(7)) * 10 + 10 for _ in range(n)]
    demo_sortk(ils, rls, plot)


def events_io(events: Dict[str, list[float]], matchs: list[str]) -> list[list[float]]:
    def nonn(x):
        return "".join([i for i in x if not i.isdigit()])

    def evnorm(x: list[float]) -> list[float]:
        assert len(x) <= 1
        return [inf] if x == [] else x

    evks = sorted(events.keys())
    groupks = {
        k: sum([evnorm(events[x]) for x in v], []) for k, v in groupby(evks, nonn)
    }
    evio = [groupks[x] for x in matchs]
    return evio


def check_out(x, r, o, ro):
    delta = 0.2
    n = len(x)
    hn = n // 2
    depth = (hn * (hn + 1)) // 2
    sdelta = depth * delta
    # print(f"{sdelta=}")
    order = list(argsort(x))
    rbool = [x < inf for x in r]
    robool = [x < inf for x in ro]
    maxdelta = max(map(sub, o, o[1:]))
    # print(f"{maxdelta=}")
    assert maxdelta <= sdelta
    if sum(rbool) == 0:
        print("no returns")
        return
    ordered_robool = [robool[i] for i in order]
    oughts = [out for out, check in zip(o, ordered_robool) if check]
    haves = [out for out, check in zip(o, rbool) if check]
    # print(f"{oughts=}, {haves=}")
    diffmax = max(map(sub, oughts, haves))
    # print(f"{diffmax=}")
    assert diffmax <= sdelta
