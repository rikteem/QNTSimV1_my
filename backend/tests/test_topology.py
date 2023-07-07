from typing import Dict, List

import pytest
from generate_topology_json import generate_random_topology
from qntsim.kernel.timeline import Timeline
from qntsim.topology.node import EndNode
from qntsim.topology.topology import Topology


def test_topology():
    simulator = Timeline(stop_time=10e12, backend="Qutip")
    configuration = Topology(name="foo", timeline=simulator)
    configuration.load_config_json(config=generate_random_topology())
    assert configuration.get_virtual_graph() is not None

if __name__=="__main__":
    test_topology()