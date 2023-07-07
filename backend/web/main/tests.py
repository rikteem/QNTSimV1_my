from django.test import TestCase
from simulator.topology_funcs import e2e

# Create your tests here.


if __name__ == "__main__":
    # Testing E2E
    # network_config = {"nodes":[{"Name":"n1","Type":"service","noOfMemory":500,"memory":{"frequency":2000,"expiry":2000,"efficiency":1,"fidelity":0.93}},{"Name":"n2","Type":"end","noOfMemory":500,"memory":{"frequency":2000,"expiry":2000,"efficiency":1,"fidelity":0.93}}],"quantum_connections":[{"Nodes":["n1","n2"],"Attenuation":0.00001,"Distance":70}],"classical_connections":[{"Nodes":["n1","n1"],"Delay":0,"Distance":1000},{"Nodes":["n1","n2"],"Delay":1000000000,"Distance":1000},{"Nodes":["n2","n1"],"Delay":1000000000,"Distance":1000},{"Nodes":["n2","n2"],"Delay":0,"Distance":1000}]}
    network_config = {"nodes":[{"Name":"n1","Type":"end","noOfMemory":500,"memory":{"frequency":80e6,"expiry":-1,"efficiency":1,"fidelity":0.93}},{"Name":"n2","Type":"service","noOfMemory":500,"memory":{"frequency":80e6,"expiry":-1,"efficiency":1,"fidelity":0.93}},{"Name":"n3","Type":"service","noOfMemory":500,"memory":{"frequency":80e6,"expiry":-1,"efficiency":1,"fidelity":0.93}},{"Name":"n4","Type":"end","noOfMemory":500,"memory":{"frequency":80e6,"expiry":-1,"efficiency":1,"fidelity":0.93}}],"quantum_connections":[{"Nodes":["n1","n2"],"Attenuation":0.00001,"Distance":70},{"Nodes":["n2","n3"],"Attenuation":0.00001,"Distance":70},{"Nodes":["n3","n4"],"Attenuation":0.00001,"Distance":70}],"classical_connections":[{"Nodes":["n1","n1"],"Delay":0,"Distance":0},{"Nodes":["n1","n2"],"Delay":1000000000,"Distance":1000},{"Nodes":["n1","n3"],"Delay":1000000000,"Distance":1000},{"Nodes":["n1","n4"],"Delay":1000000000,"Distance":1000},{"Nodes":["n2","n1"],"Delay":1000000000,"Distance":1000},{"Nodes":["n2","n2"],"Delay":0,"Distance":0},{"Nodes":["n2","n3"],"Delay":1000000000,"Distance":1000},{"Nodes":["n2","n4"],"Delay":1000000000,"Distance":1000},{"Nodes":["n3","n1"],"Delay":1000000000,"Distance":1000},{"Nodes":["n3","n2"],"Delay":1000000000,"Distance":1000},{"Nodes":["n3","n3"],"Delay":0,"Distance":0},{"Nodes":["n3","n4"],"Delay":1000000000,"Distance":1000},{"Nodes":["n4","n1"],"Delay":1000000000,"Distance":1000},{"Nodes":["n4","n2"],"Delay":1000000000,"Distance":1000},{"Nodes":["n4","n3"],"Delay":1000000000,"Distance":1000},{"Nodes":["n4","n4"],"Delay":0,"Distance":0}]}
    sender = "n1"
    receiver = "n4"
    startTime = 1e12
    size = 6
    priority = 0
    targetFidelity = 0.8
    timeout = 2e12
    report = e2e(network_config, sender, receiver, startTime, size, priority, targetFidelity, timeout)
    print(report)