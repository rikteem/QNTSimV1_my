from qntsim.kernel.timeline import Timeline 
Timeline.DLCZ=False
Timeline.bk=True
from qntsim.topology.topology import Topology
from tabulate import tabulate
from application.e91 import E91
from application.teleportation import Teleportation
from application.ping_pong import PingPong
from application.ghz import GHZ
from application.qsdc1 import QSDC1
from application.ip1 import IP1

def load_topo(path,backend):

   tl = Timeline(20e12,backend)
   network_topo = Topology("network_topo", tl)
   network_topo.load_config(path)
   return tl,network_topo


def get_res(network_topo,req_pairs):

      #table=[]
      for pair in req_pairs:
         print('src ',pair[0])
         table=[]
         src=pair[0]
         for info in network_topo.nodes[src].resource_manager.memory_manager:
            if info.state == 'ENTANGLED' or info.state == 'OCCUPIED':
               table.append([info.index,src,info.remote_node,info.fidelity,info.entangle_time * 1e-12,info.entangle_time * 1e-12+info.memory.coherence_time,info.state])
         print(tabulate(table, headers=['Index','Source node', 'Entangled Node' , 'Fidelity', 'Entanglement Time' ,'Expire Time', 'State'], tablefmt='grid'))
         table=[]
         print('dst ',pair[1])
         dst=pair[1]
         for info in network_topo.nodes[dst].resource_manager.memory_manager:
            if info.state == 'ENTANGLED' or info.state == 'OCCUPIED':
               table.append([info.index,dst,info.remote_node,info.fidelity,info.entangle_time * 1e-12,info.entangle_time * 1e-12+info.memory.coherence_time,info.state])
         print(tabulate(table, headers=['Index','Source node', 'Entangled Node' , 'Fidelity', 'Entanglement Time' ,'Expire Time', 'State'], tablefmt='grid'))
      
def set_parameters(topology:Topology):
   
   MEMO_FREQ = 2e4
   MEMO_EXPIRE = 0
   MEMO_EFFICIENCY = 1
   MEMO_FIDELITY = 0.9349367588934053
   for node in topology.get_nodes_by_type("EndNode"):
      node.memory_array.update_memory_params("frequency", MEMO_FREQ)
      node.memory_array.update_memory_params("coherence_time", MEMO_EXPIRE)
      node.memory_array.update_memory_params("efficiency", MEMO_EFFICIENCY)
      node.memory_array.update_memory_params("raw_fidelity", MEMO_FIDELITY)
   
   for node in topology.get_nodes_by_type("ServiceNode"):
      node.memory_array.update_memory_params("frequency", MEMO_FREQ)
      node.memory_array.update_memory_params("coherence_time", MEMO_EXPIRE)
      node.memory_array.update_memory_params("efficiency", MEMO_EFFICIENCY)
      node.memory_array.update_memory_params("raw_fidelity", MEMO_FIDELITY)


   DETECTOR_EFFICIENCY = 0.9
   DETECTOR_COUNT_RATE = 5e7
   DETECTOR_RESOLUTION = 100
   for node in topology.get_nodes_by_type("BSMNode"):
      node.bsm.update_detectors_params("efficiency", DETECTOR_EFFICIENCY)
      node.bsm.update_detectors_params("count_rate", DETECTOR_COUNT_RATE)
      node.bsm.update_detectors_params("time_resolution", DETECTOR_RESOLUTION)
      

   SWAP_SUCC_PROB = 0.9
   SWAP_DEGRADATION = 0.99

   ATTENUATION = 1e-5
   QC_FREQ = 1e11
   for qc in topology.qchannels:
      qc.attenuation = ATTENUATION
      qc.frequency = QC_FREQ


def input_e91(e91_state):



   print("\n ----E91 QKD--- ")   
   print("\nEnter command for help page $:help")
   print("\nEnter command to Load topology $: load_topology <path_to_json_file>")
   print("\nEnter command to run E91 $:run_e91 <sender> <receiver> <keylength>")
   print("\nEnter command to exit Simulation $:exit\n")


   while True:
      user_input = input('>>>')
      tokens = user_input.split()
      command = tokens[0]
      args=tokens[1:]

      if command=='load_topology'and (e91_state==0 or e91_state==1) :
         if len(args)==1:
            print('\nLoaded topology\n')
            path=args[0]
            tl,network_topo=load_topo(path,"Qiskit")
            network_topo.get_virtual_graph()
            #print("To get keys between end nodes run_e91")
            e91_state=1
         else:
            print("Path to config file is not given\n")
      
      elif command=='run_e91':
         
         if e91_state==1:
            if len(args)==3:
               sender=args[0]
               receiver=args[1]
               keys=int(args[2])
               if keys<50 and keys>0:
                  n=int((9*keys)/2)
                  alice=network_topo.nodes[sender]
                  bob = network_topo.nodes[receiver]
                  e91=E91()
                  alice,bob=e91.roles(alice,bob,n)
                  tl.init()
                  tl.run()  
                  e91.run(alice,bob,n)
               else:
                  print("key length should be less than 50")
            else:
               print("incorrect sender or receiver or keylength") 
         else:
            print("Topology is not yet loaded ,enter command to Load topology")

      elif command=='exit':
         break

      elif command=='help':
         print("\nCommand to Load topology $: load_topology <path_to_json_file>")
         print("$:load_topology config.json")
         print("\nCommand to run E91 $:run_e91 <sender> <receiver> <keylength>")
         print("$:run_e91 endnode1 endnode2 20")
         print("\ncommand to exit Simulation $:exit\n")

      else:
         print("Enter correct command")

def ping_pong(ping_pong_state):

   print("\nEnter command for help page $:help")
   print("\nEnter command to Load topology $: load_topology <path_to_json_file>")
   print("\nEnter command to run ping pong protocol $:run_pp <sender> <receiver> <sequence_length> <message>")
   print("\nEnter command to exit Simulation $:exit\n")
   while True:

      user_input = input('>>>')
      tokens = user_input.split()
      command = tokens[0]
      args=tokens[1:]

      if command=='load_topology'and (ping_pong_state==0 or ping_pong_state==1) :
         if len(args)==1:
            print('\nLoaded topology\n')
            path=args[0]
            tl,network_topo=load_topo(path,"Qutip")
            network_topo.get_virtual_graph()
            #print("To get keys between end nodes run_e91")
            ping_pong_state=1
         else:
            print("Path to config file is not given\n")
      
      elif command=='run_pp':
         
         if ping_pong_state==1:
            if len(args)==4:
               sender=args[0]
               receiver=args[1]
               sequence_length=int(args[2])
               message=args[3]
               if len(message)<=9:
                  n=int(sequence_length*len(message))
                  alice=network_topo.nodes[sender]
                  bob = network_topo.nodes[receiver]
                  pp=PingPong()
                  alice,bob=pp.roles(alice,bob,n)
                  tl.init()
                  tl.run() 
                  pp.create_key_lists(alice,bob)
                  pp.run(sequence_length,message)
               else:
                  print("message length should be less than 9")
            else:
               print("incorrect sender or receiver or sequencelength or message") 
         else:
            print("Topology is not yet loaded ,enter command to Load topology")

      elif command=='exit':
         break

      elif command=='help':
         print("\nCommand to Load topology $: load_topology <path_to_json_file>")
         print("$:load_topology config.json")
         print("\nEnter command to run ping pong protocol $:run_pp <sender> <receiver> <sequence_length> <message>")
         print("$:run_pp endnode1 endnode2 4 010101")
         print("\ncommand to exit Simulation $:exit\n")

      else:
         print("Enter correct command")


def qsdc1(qsdc1_state):

   print("\nEnter command for help page $:help")
   print("\nEnter command to Load topology $: load_topology <path_to_json_file>")
   print("\nEnter command to run first qsdc protocol $:run_qsdc1 <sender> <receiver> <sequence_length> <key>")
   print("\nEnter command to exit Simulation $:exit\n")
   while True:

      user_input = input('>>>')
      tokens = user_input.split()
      command = tokens[0]
      args=tokens[1:]

      if command=='load_topology'and (qsdc1_state==0 or qsdc1_state==1) :
         if len(args)==1:
            print('\nLoaded topology\n')
            path=args[0]
            tl,network_topo=load_topo(path,"Qutip")
            network_topo.get_virtual_graph()
            #print("To get keys between end nodes run_e91")
            qsdc1_state=1
         else:
            print("Path to config file is not given\n")
      
      elif command=='run_qsdc1':
         
         if qsdc1_state==1:
            if len(args)==4:
               sender=args[0]
               receiver=args[1]
               sequence_length=int(args[2])
               message=args[3]
               if (len(message)%2==0):
                  
                  n=int(sequence_length*len(message))
                  alice=network_topo.nodes[sender]
                  bob = network_topo.nodes[receiver]
                  qsdc1=QSDC1()
                  alice,bob=qsdc1.roles(alice,bob,n)
                  tl.init()
                  tl.run()  
                  qsdc1.run(alice,bob,sequence_length,message)
               else:
                  print("Enter message of even length")
            else:
               print("incorrect sender or receiver or sequencelength or message") 
         else:
            print("Topology is not yet loaded ,enter command to Load topology")

      elif command=='exit':
         break

      elif command=='help':
         print("\nCommand to Load topology $: load_topology <path_to_json_file>")
         print("$:load_topology config.json")
         print("\nEnter command to run  first qsdc protocol $:run_qsdc1 <sender> <receiver> <sequence_length> <key>")
         print("$:run_qsdc1 endnode1 endnode2 4 010101")
         print("\ncommand to exit Simulation $:exit\n")

      else:
         print("Enter correct command")

def ip1(ip1_state):

   print("\nEnter command for help page $:help")
   print("\nEnter command to Load topology $: load_topology <path_to_json_file>")
   print("\nEnter command to run ip_protocol 1 $:run_ip1 <sender> <receiver> <message>")
   print("\nEnter command to exit Simulation $:exit\n")
   while True:

      user_input = input('>>>')
      tokens = user_input.split()
      command = tokens[0]
      args=tokens[1:]

      if command=='load_topology'and (ip1_state==0 or ip1_state==1) :
         if len(args)==1:
            print('\nLoaded topology\n')
            path=args[0]
            tl,network_topo=load_topo(path,"Qutip")
            network_topo.get_virtual_graph()
            #print("To get keys between end nodes run_e91")
            ip1_state=1
         else:
            print("Path to config file is not given\n")
      
      elif command=='run_ip1':
         
         if ip1_state==1:
            if len(args)==3:
               sender=args[0]
               receiver=args[1]
               message=args[2]
               
               alice=network_topo.nodes[sender]
               bob = network_topo.nodes[receiver]
               ip1=IP1()
               alice,bob=ip1.roles(alice,bob,n=50)
               tl.init()
               tl.run()  
               ip1.run(alice,bob,message)
              
            else:
               print("incorrect sender or receiver or message") 
         else:
            print("Topology is not yet loaded ,enter command to Load topology")

      elif command=='exit':
         break

      elif command=='help':
         print("\nCommand to Load topology $: load_topology <path_to_json_file>")
         print("$:load_topology config.json")
         print("\nEnter command to run ip protocol 1 $:run_ip1 <sender> <receiver> <message>")
         print("$:run_qsdc1 endnode1 endnode2 010101")
         print("\ncommand to exit Simulation $:exit\n")

      else:
         print("Enter correct command")

def input_entanglements(e2e_state):

   print("\n ----E2E entanglements--- ")  
   print("\nEnter command for help page $:help")
   print("\nEnter command for backend $:backend Qiskit/Qutip")
   print("\nEnter command to Load topology $: load_topology <path_to_json_file>")
   print("\nEnter command requesting entanglements $:")
   print("ent_req  <src node-namping_pong_statee> <dst node-name> <start_time> <size>  <priority> <target_fidelity> <timeout>")
   print("\nEnter command to run simulation $: run_sim ")    
   print("\nEnter command to get results $: get_res ")
   print("\nEnter command to exit Simulation $:exit")

   while True:
      
      print("\n")
      user_input = input('>>>')
      tokens = user_input.split()
      command = tokens[0]
      args=tokens[1:]

      if command=='backend':
         if (e2e_state==0 or e2e_state==1 or e2e_state==4 ):
            if args[0]=='Qiskit':
               backend="Qiskit"
               print("\nQiskit was selected")
               print("Enter command to Load topology $: load_topology <path_to_json_file>")

            elif args[0]=='Qutip':
               backend="Qutip"
               print("\nQutip was selected")
               print("Enter command to Load topology $: load_topology <path_to_json_file>")

            else :
               print("Enter correct command")
         else:
            print("Backend was already set")
         e2e_state=1


      elif command == 'load_topology':
         if (e2e_state==1 or e2e_state==2 ):
            if len(args)==1:
               print('\nLoaded topology')
               path=args[0]
               tl,network_topo=load_topo(path,backend)
               set_parameters(network_topo)
               req_pairs=[]
               e2e_state=2
               network_topo.get_virtual_graph()
               
               print("Enter command requesting entanglements $:")
               print(" ent_req  <src node-name> <dst node-name> <start_time> <size>  <priority> <target_fidelity> <timeout>")
            else:
               print("Path to config file is not given")
         elif(e2e_state==0):
            print("Backend was not chosen")
         


      elif command == 'ent_req':
         if (e2e_state==2 or e2e_state==3):
            if len(args)==7:
               node1=args[0]
               node2=args[1]
               start_time=(int(args[2]))*1e12
               if start_time>20 and start_time<0:
                  print("start time should be less than 20")
               else:   
                  size=args[3]
                  #end_time=(int(args[4]))*1e12
                  priority=args[4]
                  target_fidelity=args[5]
                  timeout=(int(args[6]))*1e12
                  tm=network_topo.nodes[node1].transport_manager
                  #end time of req is simulation end time
                  tm.request(node2, float(start_time),int(size), 20e12 , int(priority) ,float(target_fidelity), float(timeout) )
                  req_pairs.append((node1,node2))
                  print("Enter command to run simulation  OR ")  
                  print("Enter command to request more entanglements")
                  e2e_state=3  
            else:
               print("Incorrect request parameters")
         elif (e2e_state==0):
            print("Backend was not chosen")
         
         elif (e2e_state==1):
            print("Topology was not loaded")
      
      elif command == 'run_sim':
         if (e2e_state==3):
            tl.init()
            tl.run()
            print("Enter command to get results $: get_res ")
            e2e_state=4

         elif(e2e_state==4):
            print("Simulation ran already")

         elif(e2e_state==2):
            print("entanglement requests were not given")

         elif (e2e_state==0):
            print("Backend was not chosen")
         
         elif (e2e_state==1):
            print("Topology was not loaded")


     
      elif command == 'get_res':
         if (e2e_state==4):
            get_res(network_topo,req_pairs)
            e2e_state=0

         elif(e2e_state==3):
            print("Simulation wasnt started")
            
         elif (e2e_state==2):
            print("No request for entanglements")

         elif (e2e_state==0):
            print("Backend was not chosen")
         
         elif (e2e_state==1):
            print("Topology was not loaded")

         

      elif command == 'exit':
         break

      elif command=='help':
         print("\ncommand for backend $:backend <Qiskit/Qutip>")
         print("$:backend Qiskit")
         print("\ncommand to Load topology $: load_topology <path_to_json_file>")
         print("$:load_topology config.json")
         print("\ncommand to request entanglements ")
         print("$:ent_req  <src node-name> <dst node-name> <start_time> <size> <priority> <target_fidelity> <timeout>")
         print("$:ent_req endnode1 endnode2 5 10 0 0.5 2 ")
         print("\ncommand to run simulation $: run_sim ")    
         print("\ncommand to get results $: get_res ")
         print("\ncommand to exit Simulation $:exit\n")


      else:
         print('Enter correct command')

def telportation(tel_state):

   print("\n ----Teleportation----")   
   print("\nEnter command for help page $:help")
   print("\nEnter command to Load topology $: load_topology <path_to_json_file>")
   print("\nEnter command to run tel $:run_tel <sender> <receiver> <random_qubit_amplitud|0> > <random_qubit_amplitude|1> >")
   print("\nEnter command to exit Simulation $:exit\n")


   while True:
      user_input = input('>>>')
      tokens = user_input.split()
      command = tokens[0]
      args=tokens[1:]

      if command=='load_topology'and (tel_state==0 or tel_state==1) :
         if len(args)==1:
            print('\nLoaded topology\n')
            path=args[0]
            tl,network_topo=load_topo(path,"Qutip")
            network_topo.get_virtual_graph()
            #print("To get keys between end nodes run_e91")
            tel_state=1
         else:
            print("Path to config file is not given\n")
      
      elif command=='run_tel':
         
         if tel_state==1:
            if len(args)==4:
               sender=args[0]
               receiver=args[1]
               A_0=complex(args[2])
               A_1=complex(args[3])
               alice=network_topo.nodes[sender]
               bob = network_topo.nodes[receiver]
               tel= Teleportation()
               alice,bob=tel.roles(alice,bob)
               tl.init()
               tl.run()  
               tel.run(alice,bob,A_0,A_1)
            else:
               print("incorrect sender or receiver or random qubit amplitudes") 
         else:
            print("Topology is not yet loaded ,enter command to Load topology")

      elif command=='exit':
         break

      elif command=='help':
         print("\nCommand to Load topology $: load_topology <path_to_json_file>")
         print("$:load_topology config.json")
         print("\nCommand to run tel $:run_tel <sender> <receiver> <random_qubit_amplitud|0> > <random_qubit_amplitude|1>")
         print("$:run_tel endnode1 endnode2 0.70710678118+0j 0-0.70710678118j")
         print("\ncommand to exit Simulation $:exit\n")

      else:
         print("Enter correct command")

def ghz(ghz_state):

   print("\n ----GHZ----")   
   print("\nEnter command for help page $:help")
   print("\nEnter command to Load topology $: load_topology <path_to_json_file>")
   print("\nEnter command to run tel $:run_ghz <endnode1> <endnode2> <endnode3> <middlenode>")
   print("\nEnter command to exit Simulation $:exit\n")


   while True:
      user_input = input('>>>')
      tokens = user_input.split()
      command = tokens[0]
      args=tokens[1:]

      if command=='load_topology'and (ghz_state==0 or ghz_state==1) :
         if len(args)==1:
            print('\nLoaded topology\n')
            path=args[0]
            tl,network_topo=load_topo(path,"Qutip")
            network_topo.get_virtual_graph()
            #print("To get keys between end nodes run_e91")
            ghz_state=1
         else:
            print("Path to config file is not given\n")
      
      elif command=='run_ghz':
         
         if ghz_state==1:
            if len(args)==4:
               endnode1=args[0]
               endnode2=args[1]
               endnode3=args[2]
               middlenode=args[3]
               alice=network_topo.nodes[endnode1]
               bob = network_topo.nodes[endnode2]
               charlie=network_topo.nodes[endnode3]
               middlenode=network_topo.nodes[middlenode]
               ghz= GHZ()
               alice,bob,charlie,middlenode=ghz.roles(alice,bob,charlie,middlenode)
               tl.init()
               tl.run()  
               ghz.run(alice,bob,charlie,middlenode)
            else:
               print("incorrect endnode1 or endnode2 or endnode3 or middlenode") 
         else:
            print("Topology is not yet loaded ,enter command to Load topology")

      elif command=='exit':
         break

      elif command=='help':
         print("\nCommand to Load topology $: load_topology <path_to_json_file>")
         print("$:load_topology config.json")
         print("\nCommand to run ghz $:run_ghz <endnode1> <endnode2> <endnode3> <middlenode>")
         print("$:run_e91 endnode1 endnode2 endnode3 middlenode")
         print("\ncommand to exit Simulation $:exit\n")

      else:
         print("Enter correct command")



def main():

   print("\n-------------------------------------------------------------------")
   print("!!!!!!!!!!!!!!!!!!!!Welcome to QNTSim!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
   print("-------------------------------------------------------------------\n")

   while True :

      print("\nEnter e91 for e91 to get keys")
      print("Enter e2e for two party end-to-end Entanglements between remote Nodes")
      print("Enter tel for telportation between remote Nodes")
      print("Enter ghz for to get GHZ state at middle node")
      print("Enter ping_pong to ping_pong protocol")
      print("Enter first_qsdc for first_qsdc protocol")
      print("Enter ip1  for ip protocol 1")
      print("Enter Quit to Quit\n")

      user_input = input('>>>')
      tokens = user_input.split()
      command = tokens[0]
      
      if command=='e91':
         e91_state=0
         input_e91(e91_state)
      
      elif command=='e2e':
         e2e_state=0
         input_entanglements(e2e_state)

      elif command=='tel':
         tel_state=0
         telportation(tel_state)  

      elif command=='ghz':
         ghz_state=0
         ghz(ghz_state)

      elif command=='ping_pong':
         ping_pong_state=0
         ping_pong(ping_pong_state)

      elif command=='first_qsdc':
         qsdc1_state=0
         qsdc1(qsdc1_state)

      elif command=='ip1':
         ip1_state=0
         ip1(ip1_state)


      elif command=='Quit':         
         break
   
      else:
         print("Enter correct command")
        
main()
