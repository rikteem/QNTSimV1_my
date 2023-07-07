import math
from collections import deque
from functools import reduce
from typing import Any, Callable, Dict, List, Tuple, Union

from ..components.circuit import QutipCircuit
from ..kernel.entity import Entity
from ..kernel.timeline import Timeline
from ..topology.node import EndNode, ServiceNode
from ..topology.topology import Topology
from .circuits import bell_type_state_analyzer, xor_type_state_analyzer
from .NoiseModel import noise_model
from .utils import to_binary, to_string


class Network(Entity):
    _obj:'Network' = None
    _flow:List[Callable] = []

    def __init__(self, name:str, topology:Dict, messages, stop_time:float, backend:str="Qutip", formalism:str="ket_vector", require_entanglements:bool=True, timeout:int=10e12, **kwargs) -> None:
        self.__timeout = timeout
        self.messages = messages
        self.__is_binary, self._bin_strs = to_binary()
        self.__dict__.update(kwargs)
        # if hasattr(self, "size"):
        #     if 
        Entity(name=name or self.__class__.__name__, timeline=Timeline(stop_time=stop_time, backend=backend, formalism=formalism))
        self.owner = self
        self.__configuration = Topology(name=self.name, timeline=self.timeline)
        load_topology = self.__configuration.load_config_json if "nodes" in topology else self.__configuration.load_config
        load_topology(config=topology)
        for _, node in self.__configuration.nodes.items():
            node.keys = [info.memory.qstate_key for info in node.memory_array if type(node) in [EndNode, ServiceNode]]
        # if require_entanglements:
        #     self._request_entanglements()
        #     self.__simulator.init()
        #     self.__simulator.run()
        #     self._identify_entanglements()
        # else:
        #     self._initialize_photons()

    def __iter__(self):
        return iter(self.__configuration.get_nodes_by_type("EndNode"))

    def __getitem__(self, item):
        return self.__configuration.nodes.get(item)

    def __call__(self, id_:int=0) -> Any:
        self.id = id_
        self.name += id_
        return reduce(function=lambda ret, func:func(self, ret), sequence=self._flow, initial=())

    def __repr__(self) -> str:
        return "\n".join(
            [
                f"Memory keys of: {node.owner.name}\n"
                + "\n".join(
                    [
                        f"{state.keys}\t{state.state}"
                        for state in [
                            self.manager.get(info.memory.qstate_key)
                            for info in node.memory_array
                        ]
                    ]
                )
                for node in self
            ]
        )

    def _request_entanglements(self,
                               src_node:EndNode,
                               dst_node:EndNode,
                               demand_size:int,
                               *,
                               start_time:int=0,
                               end_time=10e12,
                               priority:int=0,
                               target_fidelity:float=1):
        transport_manager = src_node.transport_manager
        transport_manager.request(responder=dst_node.name,
                                  start_time=start_time,
                                  size=demand_size,
                                  end_time=end_time,
                                  priority=priority,
                                  target_fidelity=target_fidelity,
                                  timeout=self.__timeout)
        self.timeline.init()
        self.timeline.run()
        num_epr = sum([1 for info in src_node.memory_array if info.state == "ENTANGLED"])
        if num_epr < demand_size:
            self._request_entanglements(src_node=src_node, dst_node=dst_node, demand_size=demand_size-num_epr)

    def _apply_noise(self, noise:str, qtc:QutipCircuit, keys:List[int]=None):
        model = noise_model()
        match noise:
            case "reset":
                try:
                    model.add_reset_error(err=self.reset)
                    return model._apply_reset_error(crc=qtc, size=qtc.size)
                except:
                    return qtc
            case "readout":
                try:
                    model.add_readout_error(err=self.readout)
                finally:
                    return model._apply_readout_error_qntsim(crc=qtc, manager=self.timeline.quantum_manager, keys=keys)

    def _encode(self, src_node:EndNode, dst_node:EndNode):
        pass

    def _densecode(self, src_node:EndNode, dst_node:EndNode):
        pass

    def _teleport(self, _, /):
        meas_results = {}
        alpha = complex(1/math.sqrt(2))
        bsa = bell_type_state_analyzer(2)
        for nodes, bin_str in self._bin_strs.items():
            src_node = nodes[0]
            dst_nodes = nodes[1:]
            for dst_node in dst_nodes:
                self._request_entanglements(src_node=src_node, dst_node=dst_node, demand_size=len(bin_str))
            if len(dst_nodes)>1:
                self._get_state()
        return meas_results

    # def _get_state(self, state:str, nodes:List[EndNode]):
    #     topology = {node_name:node.neighbors for node_name, node in self.__configuration.nodes.items() if node.__class__ in [EndNode, ServiceNode]}
    #     routes = [self._find_route(src_node=src_node.name, dst_node=dst_node.name, topology=topology) for src_node, dst_node in zip(nodes[:-1], nodes[1:])]
    #     service_nodes = self._extract_service_nodes(routes=routes)
    #     for service_node in service_nodes:
    #         neighbour_nodes = service_node.neighbors
    #         self._swap_entanglement(node=service_node)

    def _swap_entanglement(self, state:str, current_node:ServiceNode, neighbor_nodes:List[Union[EndNode, ServiceNode]], qtc:QutipCircuit):
        current_keys = [info.memory.qstate_key for info in current_node.memory_array if info.state=="ENTANGLED"]
        neighbor_keys = [[self.timeline.quantum_manager.get(info.memory.qstate_key).keys for info in neighbor_node.memory_array if info.state=="ENTANGLED"] for neighbor_node in neighbor_nodes]
        circuit = (
            bell_type_state_analyzer(len(neighbor_nodes)) if state == "ghz" else
            xor_type_state_analyzer(len(neighbor_nodes)) if state == "xor" else
            qtc
            )
        for entangled_keys in zip(*neighbor_keys):
            swap_keys = []
            for ent_keys in entangled_keys:
                swap_keys.append(set(ent_keys) & set(current_keys))
            swap_keys.sort()
            results = self.timeline.quantum_manager.run_circuit(circuit=circuit, keys=swap_keys)
            for key in swap_keys:
                pass

    def _extract_service_nodes(self, routes:List[List[str]]):
        service_nodes = set()
        for route in routes:
            for node in route[1:-1]:
                service_nodes.add(node)
        return list(service_nodes)

    def _find_route(src_node:str, dst_node:str, topology:Dict[str, List[str]]):
        visited = set()
        queue = deque([(src_node, [])])
        while queue:
            current_node, path = queue.popleft()
            if current_node == dst_node:
                return path + [current_node]
            visited.add(current_node)
            neighbours = topology.get(current_node, [])
            for neighbour in neighbours:
                if neighbour not in neighbours:
                    queue.append((neighbour, path+[current_node]))

    def _meas_all(self, meas_results:Dict[Tuple, List[int]], /):
        for key, val in meas_results.items():
            qtc = QutipCircuit(1)
            qtc = self._apply_noise(noise="reset", qtc=qtc)
            if val[1]:
                qtc.x(0)
            if val[0]:
                qtc.z(0)
            qtc.h(0)
            qtc.measure(0)

    def _decode(self, ):
        pass

    @classmethod
    def load_topology(cls, topology:Dict, messages, stop_time:float, backend:str="Qutip", formalism:str="ket_vector", require_entanglements:bool=True, timeout:int=10e12, **kwargs):
        cls._obj = cls(topology=topology, messages=messages, stop_time=stop_time, backend=backend, formalism=formalism, require_entanglements=require_entanglements, timeout=timeout, **kwargs)
        return cls._obj

    @staticmethod
    def encode(message):
        pass

    @staticmethod
    def decode():
        pass

    def execute():
        pass