# pylint: disable=no-member
from abc import abstractmethod
from collections import namedtuple
from typing import Tuple
from pylse.pylse_exceptions import PylseError
from pylse.core import Wire
from pylse.sfq_cells import SFQ

class JTL(SFQ):
    """Josephson Transmission Line

    Default numbers for JJs and Firing Delay come from [1] (page 9 prose)
    """

    name = "JTL"
    inputs = ["a"]
    outputs = ["q"]
    transitions = [
        {"source": "idle", "trigger": "a", "dest": "idle", "firing": "q"},
    ]
    jjs = 2
    firing_delay = 4.6


class C(SFQ):
    """C Element

    Default numbers come from [1] (Table 1, LA cell).
    """

    name = "C"
    inputs = ["a", "b"]
    outputs = ["q"]
    firing_delay = 7
    transitions = [
        {
            "id": "0",
            "source": "idle",
            "trigger": "a",
            "dest": "a_arrived",
            "priority": 0,
        },
        {
            "id": "1",
            "source": "idle",
            "trigger": "b",
            "dest": "b_arrived",
            "priority": 0,
        },
        {
            "id": "2",
            "source": "a_arrived",
            "trigger": "b",
            "dest": "idle",
            "firing": "q",
            "transition_time": firing_delay,
        },
        {"id": "3", "source": "a_arrived", "trigger": "a", "dest": "a_arrived"},
        {
            "id": "4",
            "source": "b_arrived",
            "trigger": "a",
            "dest": "idle",
            "firing": "q",
            "transition_time": firing_delay,
        },
        {"id": "5", "source": "b_arrived", "trigger": "b", "dest": "b_arrived"},
    ]
    jjs = 4


class C_INV(SFQ):
    """Inverted C Element

    Default numbers for JJs and Firing Delay come from [1] (3 redundant JJs were removed from [3]
    to get to this number).
    """

    name = "C_INV"
    inputs = ["a", "b"]
    outputs = ["q"]
    firing_delay = 7
    _reset_time = 5.0
    # NOTE: We're explicitly putting transition 2 before 3 to mean we've prioritized handling
    # 'a' if both 'a' and 'b' arrive at the exact same time; likewise, putting transition 4 before
    # 5 means we've prioritized handling 'b' if both 'a' and 'b' arrive at the exact same time.
    transitions = [
        {
            "id": "0",
            "source": "idle",
            "trigger": "a",
            "dest": "a_arrived",
            "firing": "q",
        },
        {
            "id": "1",
            "source": "idle",
            "trigger": "b",
            "dest": "b_arrived",
            "firing": "q",
        },
        {"id": "2", "source": "a_arrived", "trigger": "a", "dest": "a_arrived"},
        {
            "id": "3",
            "source": "a_arrived",
            "trigger": "b",
            "dest": "idle",
            "transition_time": _reset_time,
        },
        {"id": "4", "source": "b_arrived", "trigger": "b", "dest": "b_arrived"},
        {
            "id": "5",
            "source": "b_arrived",
            "trigger": "a",
            "dest": "idle",
            "transition_time": _reset_time,
        },
    ]
    jjs = 4


class M(SFQ):
    """Merger Element

    Default numbers for JJs and Firing Delay come from [2].
    Transition time comes from the fact that if you receive an input while firing,
    you'd normally want that to be an error since that input pulse is usually phyiscally
    swallowed up.
    """

    name = "M"
    inputs = ["a", "b"]
    outputs = ["q"]
    firing_delay = 8.3
    # Cant have hold time in merge tree
    # _hold_time = 5
    _hold_time = 0
    transitions = [
        {
            "source": "idle",
            "trigger": "a",
            "firing": "q",
            "dest": "idle",
            "transition_time": _hold_time,
        },
        {
            "source": "idle",
            "trigger": "b",
            "firing": "q",
            "dest": "idle",
            "transition_time": _hold_time,
        },
    ]
    jjs = 5


class S(SFQ):
    """Splitter Element

    Default numbers for JJs and Firing Delay come from [1].
    These also agree with the numbers from [2].
    """

    name = "S"
    inputs = ["a"]
    outputs = ["l", "r"]
    firing_delay = 5.1
    transitions = [
        {
            "source": "idle",
            "trigger": "a",
            "dest": "idle",
            "firing": ["l", "r"],
            "transition_time": 7.0,
        },
    ]
    jjs = 3


###############
# Flip Flops  #
###############


class INH(SFQ):
    """Inhibitor (binary not temporal) implemented via DRO"""

    _setup_time = 0.0
    # Hold time is not 2.4 because we dont care about case with existing data pulse stored
    # Not 0.6 because temporaly the hold time violation just means both signals get triggered,
    # so we can deal with that tie by showing it works even for the case the signals arrive exactly
    # together
    _hold_time = 0  # 0.6

    name = "INH"
    inputs = ["a", "clk"]
    outputs = ["q"]
    transitions = [
        {"id": "0", "source": "idle", "trigger": "a", "dest": "a_arrived"},
        {
            "id": "1",
            "source": "idle",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {"id": "2", "source": "a_arrived", "trigger": "a", "dest": "a_arrived"},
        {
            "id": "3",
            "source": "a_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
    ]
    jjs = 4 # to reflect DROSR's cost
    firing_delay = 3.6


class DRO(SFQ):
    """Destructive read-out (AKA DFF) element"""

    _setup_time = 0.0
    _hold_time = 2.4

    name = "DRO"
    inputs = ["a", "clk"]
    outputs = ["q"]
    transitions = [
        {"id": "0", "source": "idle", "trigger": "a", "dest": "a_arrived"},
        {
            "id": "1",
            "source": "idle",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {"id": "2", "source": "a_arrived", "trigger": "a", "dest": "a_arrived"},
        {
            "id": "3",
            "source": "a_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
    ]
    jjs = 4
    firing_delay = 3.6


class DRO2R(SFQ):
    """Destructive read-out (AKA DFF) element"""

    _setup_time = 0.0
    _hold_time = 4.1

    name = "DRO2R"
    inputs = ["a", "clk", "clk2"]
    outputs = ["q", "w"]
    transitions = [
        {"id": "0", "source": "idle", "trigger": "a", "dest": "a_arrived"},
        {
            "id": "1",
            "source": "idle",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {
            "id": "12",
            "source": "idle",
            "trigger": "clk2",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {"id": "2", "source": "a_arrived", "trigger": "a", "dest": "a_arrived"},
        {
            "id": "3",
            "source": "a_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
        {
            "id": "32",
            "source": "a_arrived",
            "trigger": "clk2",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "w",
        },
    ]
    jjs = 6
    firing_delay = 6.6


class PTL(SFQ):
    """Passive Transmission Line

    A wire routing pulses from input to output and Firing Delay come from [1] (page 9 prose)
    """

    name = "PTL"
    inputs = ["a"]
    outputs = ["q"]
    transitions = [
        {"source": "idle", "trigger": "a", "dest": "idle", "firing": "q"},
    ]
    jjs = 0
    firing_delay = 25


class NDRO(SFQ):
    """NON Destructive read-out element with set-reset inputs."""

    _setup_time = 0.0
    _hold_time = 0.0

    name = "NDRO"
    inputs = ["set", "rst", "clk"]
    outputs = ["q"]
    transitions = [
        {
            "id": "0",
            "source": "idle",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {"id": "1", "source": "idle", "trigger": "rst", "dest": "idle"},
        {"id": "2", "source": "idle", "trigger": "set", "dest": "set_arrived"},
        {"id": "3", "source": "set_arrived", "trigger": "set", "dest": "set_arrived"},
        {"id": "4", "source": "set_arrived", "trigger": "rst", "dest": "idle"},
        {
            "id": "5",
            "source": "set_arrived",
            "trigger": "clk",
            "dest": "set_arrived",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
    ]
    jjs = 11
    firing_delay = 5.5


class DRO_SR(SFQ):
    """Destructive read-out element with set-reset inputs.

    Currently just using similar numbers from DRO.
    """

    _setup_time = 1.2
    _hold_time = 0.0

    name = "DRO_SR"
    inputs = ["set", "rst", "clk"]
    outputs = ["q"]
    transitions = [
        {
            "id": "0",
            "source": "idle",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {"id": "1", "source": "idle", "trigger": "rst", "dest": "idle"},
        {"id": "2", "source": "idle", "trigger": "set", "dest": "set_arrived"},
        {"id": "3", "source": "set_arrived", "trigger": "set", "dest": "set_arrived"},
        {"id": "4", "source": "set_arrived", "trigger": "rst", "dest": "idle"},
        {
            "id": "5",
            "source": "set_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
    ]
    jjs = 13
    firing_delay = 5.1


class DRO_C(SFQ):
    """Destructive read-out element with complementary outputs (AKA DFF with compl. outputs)

    Currently just using similar numbers from DRO.
    """

    _setup_time = 1.2
    _hold_time = 0.0

    name = "DRO_C"
    inputs = ["a", "clk"]
    outputs = ["q", "qnot"]
    transitions = [
        {"id": "0", "source": "idle", "trigger": "a", "dest": "a_arrived"},
        {
            "id": "1",
            "source": "idle",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "qnot",
        },
        {"id": "2", "source": "a_arrived", "trigger": "a", "dest": "a_arrived"},
        {
            "id": "3",
            "source": "a_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
    ]
    jjs = 13
    firing_delay = 9.5


##########################################################################
# Synchronous                                                            #
#                                                                        #
# Here, "synchronous" means that each element takes in at least an input #
# that is commonly connected to a synchronizing clock.                   #
##########################################################################
class INV(SFQ):
    """Sync. inverter element

    Numbers for come from Nagaoka 2019 [2].
    """

    _setup_time = 2.1
    _hold_time = 4.5

    name = "INV"
    inputs = ["a", "clk"]
    outputs = ["q"]
    transitions = [
        {
            "id": "0",
            "source": "idle",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
        {"id": "1", "source": "idle", "trigger": "a", "dest": "a_arrived"},
        {
            "id": "2",
            "source": "a_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {"id": "3", "source": "a_arrived", "trigger": "a", "dest": "a_arrived"},
    ]
    jjs = 8
    firing_delay = 5.5


class AND(SFQ):
    """Sync. AND element

    Default numbers for JJs, setup time, and firing delay come from [1] (Table III and prose);
    I've set an arbitrary number a little larger than setup time for the hold time.
    Setup and hold time come from [2] (Figure 29.3.1) (it also uses: 7.9 for
    firing delay and has 14 JJs)
    """

    _setup_time = 1.6  # Time before clock during which no inputs are allowed
    _hold_time = 1.6  # Time after clock during which no inputs are allowed

    name = "AND"
    inputs = ["a", "b", "clk"]
    outputs = ["q"]
    transitions = [
        {
            "id": "0",
            "source": "idle",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {"id": "1", "source": "idle", "trigger": "a", "dest": "a_arrived"},
        {"id": "2", "source": "idle", "trigger": "b", "dest": "b_arrived"},
        {"id": "3", "source": "a_arrived", "trigger": "b", "dest": "a_and_b_arrived"},
        {"id": "4", "source": "a_arrived", "trigger": "a", "dest": "a_arrived"},
        {
            "id": "5",
            "source": "a_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {"id": "6", "source": "b_arrived", "trigger": "a", "dest": "a_and_b_arrived"},
        {
            "id": "7",
            "source": "b_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {"id": "8", "source": "b_arrived", "trigger": "b", "dest": "b_arrived"},
        {
            "id": "9",
            "source": "a_and_b_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
        {
            "id": "10",
            "source": "a_and_b_arrived",
            "trigger": ["a", "b"],
            "dest": "a_and_b_arrived",
        },
    ]
    jjs = 11
    firing_delay = 5.0


class OR(SFQ):
    """Sync. OR element

    Default numbers for JJs and firing delay come from [1].
    Setup/hold time comes from [2].
    """

    _setup_time = 3.8
    _hold_time = 3.8  # copied ct_a_clk for both

    name = "OR"
    inputs = ["a", "b", "clk"]
    outputs = ["q"]
    transitions = [
        {"id": "0", "source": "idle", "trigger": ["a", "b"], "dest": "a_or_b_arrived"},
        {
            "id": "1",
            "source": "idle",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {
            "id": "2",
            "source": "a_or_b_arrived",
            "trigger": ["a", "b"],
            "dest": "a_or_b_arrived",
        },
        {
            "id": "3",
            "source": "a_or_b_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
    ]
    jjs = 12
    firing_delay = 5.5


class XOR(SFQ):
    """Sync. XOR element

    Default numbers come from [2].
    """

    _setup_time = 7.3
    _hold_time = 6.1

    name = "XOR"
    inputs = ["a", "b", "clk"]
    outputs = ["q"]
    transitions = [
        # Order if simultaneous is based on order of transitions given for a given source,
        # meaning here, while in 'idle', 'a' will be handled first, then 'b', then finally 'clk',
        # if they arrive simultaneously.
        {"id": "0", "source": "idle", "trigger": "a", "dest": "a_arrived"},
        {"id": "1", "source": "idle", "trigger": "b", "dest": "b_arrived"},
        {
            "id": "2",
            "source": "idle",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {"id": "3", "source": "a_arrived", "trigger": "a", "dest": "a_arrived"},
        {"id": "4", "source": "a_arrived", "trigger": "b", "dest": "idle"},
        {
            "id": "5",
            "source": "a_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
        {"id": "6", "source": "b_arrived", "trigger": "b", "dest": "b_arrived"},
        {"id": "7", "source": "b_arrived", "trigger": "a", "dest": "idle"},
        {
            "id": "8",
            "source": "b_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
    ]
    jjs = 11
    firing_delay = 5.0


class XNOR(SFQ):
    """Sync. XNOR element

    Default JJ numbers come from [4].
    """

    _setup_time = 7.4 + 1e-2
    _hold_time = 7.7

    name = "XNOR"
    inputs = ["a", "b", "clk"]
    outputs = ["q"]
    transitions = [
        {"id": "0", "source": "idle", "trigger": "a", "dest": "a_arrived"},
        {"id": "1", "source": "idle", "trigger": "b", "dest": "b_arrived"},
        {
            "id": "2",
            "source": "idle",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
        {"id": "3", "source": "a_arrived", "trigger": "a", "dest": "a_arrived"},
        {"id": "4", "source": "a_arrived", "trigger": "b", "dest": "a_and_b_arrived"},
        {
            "id": "5",
            "source": "a_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {"id": "6", "source": "b_arrived", "trigger": "b", "dest": "b_arrived"},
        {"id": "7", "source": "b_arrived", "trigger": "a", "dest": "a_and_b_arrived"},
        {
            "id": "8",
            "source": "b_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
        },
        {
            "id": "9",
            "source": "a_and_b_arrived",
            "trigger": "b",
            "dest": "a_and_b_arrived",
        },
        {
            "id": "10",
            "source": "a_and_b_arrived",
            "trigger": "a",
            "dest": "a_and_b_arrived",
        },
        {
            "id": "11",
            "source": "a_and_b_arrived",
            "trigger": "clk",
            "dest": "idle",
            "transition_time": _hold_time,
            "past_constraints": {"*": _setup_time},
            "firing": "q",
        },
    ]
    jjs = 19
    firing_delay: float = 14.3


# class NAND(SFQ):
#    ''' Sync. NAND element
#
#    Default JJ numbers come from [4].
#    '''
#    _setup_time = 5.0
#    _hold_time = 0.0
#
#    name = 'NAND'
#    inputs = ['a', 'b', 'clk']
#    outputs = ['q']
#    transitions = [
#        # Order if simultaneous is based on order of transitions given for a given source,
#        # meaning here, while in 'idle', 'a' will be handled first, then 'b', then finally 'clk',
#        # if they arrive simultaneously.
#        {'id': '0',  'source': 'idle',      'trigger': 'a',   'dest': 'a_arrived'},
#        {'id': '1',  'source': 'idle',      'trigger': 'b',   'dest': 'b_arrived'},
#        {'id': '2',  'source': 'idle',      'trigger': 'clk', 'dest': 'idle',
#         'transition_time': _hold_time, 'past_constraints': {'*': _setup_time},
#         'firing': 'q'},
#
#        {'id': '3',  'source': 'a_arrived', 'trigger': 'a',   'dest': 'a_arrived'},
#        {'id': '4',  'source': 'a_arrived', 'trigger': 'b',   'dest': 'a_and_b_arrived'},
#        {'id': '5',  'source': 'a_arrived', 'trigger': 'clk', 'dest': 'idle',
#         'transition_time': _hold_time, 'past_constraints': {'*': _setup_time},
#         'firing': 'q'},
#
#        {'id': '6',  'source': 'b_arrived', 'trigger': 'b',   'dest': 'b_arrived'},
#        {'id': '7',  'source': 'b_arrived', 'trigger': 'a',   'dest': 'a_and_b_arrived'},
#        {'id': '8',  'source': 'b_arrived', 'trigger': 'clk', 'dest': 'idle',
#         'transition_time': _hold_time, 'past_constraints': {'*': _setup_time},
#         'firing': 'q'},
#
#        {'id': '9',  'source': 'a_and_b_arrived', 'trigger': 'b',   'dest': 'a_and_b_arrived'},
#        {'id': '10', 'source': 'a_and_b_arrived', 'trigger': 'a',   'dest': 'a_and_b_arrived'},
#        {'id': '11', 'source': 'a_and_b_arrived', 'trigger': 'clk', 'dest': 'idle',
#         'transition_time': _hold_time, 'past_constraints': {'*': _setup_time}},
#    ]
#    jjs = 16
#    firing_delay = 5.0
#
#
# class NOR(SFQ):
#    ''' Sync. NOR element
#
#    Default JJ numbers come from [4].
#    '''
#    _setup_time = 5.0
#    _hold_time = 0.0
#
#    name = 'NAND'
#    inputs = ['a', 'b', 'clk']
#    outputs = ['q']
#    transitions = [
#        {'id': '0',  'source': 'idle',      'trigger': 'a',   'dest': 'a_or_b_arrived'},
#        {'id': '1',  'source': 'idle',      'trigger': 'b',   'dest': 'a_or_b_arrived'},
#        {'id': '2',  'source': 'idle',      'trigger': 'clk', 'dest': 'idle',
#         'transition_time': _hold_time, 'past_constraints': {'*': _setup_time},
#         'firing': 'q'},
#
#        {'id': '3',  'source': 'a_or_b_arrived', 'trigger': 'a',   'dest': 'a_or_b_arrived'},
#        {'id': '4',  'source': 'a_or_b_arrived', 'trigger': 'b',   'dest': 'a_or_b_arrived'},
#        {'id': '5',  'source': 'a_or_b_arrived', 'trigger': 'clk', 'dest': 'idle',
#         'transition_time': _hold_time, 'past_constraints': {'*': _setup_time}},
#    ]
#    jjs = 12
#    firing_delay = 5.0


# For all of these helpers, the **option dictionary argument can take the following:
# - jjs (int): number of JJs in the cell
# - firing_delay (float/dict): firing delay in the cell (per output per transition if dict given)
# - transition_time (float/dict): transition time for each transition already set to have
#   a non-zero transition time (transition time per transition if dict passed in)
# - error_transitions (set[str]): set of the transitions which should be considered erroneous


def jtl(in0: Wire, name=None, **overrides):
    """Create and connect a JTL

    :param Wire in0: input wire
    :param str name: Name to give the output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    """
    from pylse.circuit import working_circuit

    out = Wire(name)
    working_circuit().add_node(JTL(**overrides), [in0], [out])
    return out


def c(in0: Wire, in1: Wire, name=None, **overrides):
    """Create and connect an C element

    :param Wire in0: first input
    :param Wire in1: second input
    :param str name: Name to give the output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    """
    from pylse.circuit import working_circuit

    out = Wire(name)
    working_circuit().add_node(C(**overrides), [in0, in1], [out])
    return out


def c_inv(in0: Wire, in1: Wire, name=None, **overrides):
    """Create and connect an C_INV element

    :param Wire in0: first input
    :param Wire in1: second input
    :param str name: Name to give the output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    """
    from pylse.circuit import working_circuit

    out = Wire(name)
    working_circuit().add_node(C_INV(**overrides), [in0, in1], [out])
    return out


def m(in0: Wire, in1: Wire, name=None, **overrides):
    """Create and connect an M element

    :param Wire in0: first input
    :param Wire in1: second input
    :param str name: Name to give the output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    """
    from pylse.circuit import working_circuit

    out = Wire(name)
    working_circuit().add_node(M(**overrides), [in0, in1], [out])
    return out


def s(in0: Wire, left_name=None, right_name=None, **overrides):
    """Create and connect a single splitter element

    :param Wire in0: wire to split
    :param str left_name: Name to give the left output wire
    :param str right_name: Name to give the right output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    :return namedtuple: a tuple for accessing the outputs, .left and .right
    """
    from pylse.circuit import working_circuit

    S_out = namedtuple("S_out", ["out1", "out2"])
    out1, out2 = Wire(left_name), Wire(right_name)
    working_circuit().add_node(S(**overrides), [in0], [out1, out2])
    return S_out(out1=out1, out2=out2)


def dro(in0: Wire, clk: Wire, name=None, **overrides):
    """Create and connect a DRO

    :param Wire in0: input wire
    :param Wire clk: input wire traditionally corresponding to a clock signal
    :param str name: Name to give the output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    :return: output wire from the DRO element
    """
    from pylse.circuit import working_circuit

    out = Wire(name)
    working_circuit().add_node(DRO(**overrides), [in0, clk], [out])
    return out


def dro_sr(sett: Wire, rst: Wire, clk: Wire, name=None, **overrides):
    """Create and connect a DRO_SR

    :param Wire sett: input wire traditionally corresponding to a set signal
    :param Wire rst: input wire traditionally corresponding to a reset signal
    :param Wire clk: input wire traditionally corresponding to a clock signal
    :param str name: Name to give the output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    :return: output wire from the DRO_SR element
    """
    from pylse.circuit import working_circuit

    out = Wire(name)
    working_circuit().add_node(DRO_SR(**overrides), [sett, rst, clk], [out])
    return out


def dro_c(in0: Wire, clk: Wire, name_q=None, name_q_not=None, **overrides):
    """Create and connect a DRO_C

    :param Wire in0: input wire
    :param Wire clk: input wire traditionally corresponding to a clock
    :param str name_q: Name to give the q output wire
    :param str name_q_not: Name to give the q_not output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    :return namedtuple: a tuple for accessing the outputs, .q and .q_not
    """
    from pylse.circuit import working_circuit

    DRO_C_out = namedtuple("DRO_C_out", ["q", "q_not"])
    q, q_not = Wire(name_q), Wire(name_q_not)
    working_circuit().add_node(DRO_C(**overrides), [in0, clk], [q, q_not])
    return DRO_C_out(q=q, q_not=q_not)


def inv(in0: Wire, clk: Wire, name=None, **overrides):
    """Create and connect an inverter element

    :param Wire in0: input wire
    :param Wire clk: input wire traditionally corresponding to a clock
    :param str name: Name to give the output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    :return: output wire from the INV element
    """
    from pylse.circuit import working_circuit

    out = Wire(name)
    working_circuit().add_node(INV(**overrides), [in0, clk], [out])
    return out


def and_s(in0: Wire, in1: Wire, clk: Wire, name=None, **overrides):
    """Create and connect a synchronous AND element

    :param Wire in0: first input wire
    :param Wire in1: second input wire
    :param Wire clk: input wire traditionally corresponding to a clock
    :param str name: Name to give the output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    :return: output wire from the AND element
    """
    from pylse.circuit import working_circuit

    out = Wire(name)
    working_circuit().add_node(AND(**overrides), [in0, in1, clk], [out])
    return out


def or_s(in0: Wire, in1: Wire, clk: Wire, name=None, **overrides):
    """Create and connect a synchronous OR element

    :param Wire in0: first input wire
    :param Wire in1: second input wire
    :param Wire clk: input wire traditionally corresponding to a clock
    :param str name: Name to give the output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    :return: output wire from the OR element
    """
    from pylse.circuit import working_circuit

    out = Wire(name)
    working_circuit().add_node(OR(**overrides), [in0, in1, clk], [out])
    return out


def xor_s(in0: Wire, in1: Wire, clk: Wire, name=None, **overrides):
    """Create and connect a synchronous XOR element

    :param Wire in0: first input wire
    :param Wire in1: second input wire
    :param Wire clk: input wire traditionally corresponding to a clock
    :param str name: Name to give the output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    :return: output wire from the XOR element
    """
    from pylse.circuit import working_circuit

    out = Wire(name)
    working_circuit().add_node(XOR(**overrides), [in0, in1, clk], [out])
    return out


def xnor_s(in0: Wire, in1: Wire, clk: Wire, name=None, **overrides):
    """Create and connect a synchronous XNOR element

    :param Wire in0: first input wire
    :param Wire in1: second input wire
    :param Wire clk: input wire traditionally corresponding to a clock
    :param str name: Name to give the output wire
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    :return: output wire from the XNOR element
    """
    from pylse.circuit import working_circuit

    out = Wire(name)
    working_circuit().add_node(XNOR(**overrides), [in0, in1, clk], [out])
    return out


def split(w, n=2, names=None, **overrides) -> Tuple[Wire, ...]:
    """Split a wire n ways, by creating n-1 splitter elements in a binary tree

    :param Wire w: wire to split
    :param int n: number of wires to return
    :param Union[list[str], str] names: list of names to give each output wire; if given,
        must be equal in length to n. Can also be a string of whitespace-separated names.
        The order of the names is left-to-right order of the resulting splitter tree.
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    :return: n new wires originating from w
    """
    if names:
        if isinstance(names, str):
            names = names.split(" ")
        if len(names) != n:
            raise PylseError(
                "Number of names given does not equal number of "
                "output wires produced."
            )
    else:
        names = [None] * n

    def f(w, n, names):
        if n == 1:
            return (w,)
        else:
            ln = n // 2
            rn = n - ln
            assert len(names) >= 2
            left_name = names[0] if ln == 1 else None
            right_name = names[1] if rn == 1 else None
            w1, w2 = s(w, left_name=left_name, right_name=right_name, **overrides)
            return f(w1, ln, names[:ln]) + f(w2, rn, names[ln:])

    return f(w, n, names)


def jtl_chain(w: Wire, n: int, names=[], **overrides) -> Wire:
    """Create a chain of n JTL elements

    :param Wire w: wire to enter the first JTL in the chain
    :param int n: number of JTLs in the chain
    :param Union[list[str], str] names: names for each wire resulting from
        the last len(names) JTLs in the chain. If names is a string, it's assumed that each
        individual name is separated by whitespace; thus, you can do names='foo' to give the
        last wire a name 'foo'.
    :param dict overrides: keyword arguments for overriding defaults of the element,
        such as: jjs, firing_delay, transition_time, error_transitions.
    :return: wire coming out of the final JTL
    """
    if names:
        if isinstance(names, str):
            names = names.split(" ")
        if len(names) > n:
            raise PylseError("Too many names given for jtl_chain wires.")

    names = [None] * (n - len(names)) + names
    for ix in range(n):
        w = jtl(w, names[ix], **overrides)
    return w
