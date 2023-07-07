from typing import Any, Dict

from ..kernel.entity import Entity


class CONetR:
    def __init__(self, name:str, topology:Dict) -> None:
        self.__name = name or self.__name__

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass
    
    @staticmethod
    def execute(topology:Dict, app_settings:Dict):
        response = {}
        netcor = CONetR(name="network", topology=topology)
        recv_msgs, avg_err, std_dev, info_leak, msg_fidelity = netcor()
        return response