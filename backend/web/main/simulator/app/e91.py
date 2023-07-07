import numpy as np
from qntsim.components.circuit import BaseCircuit
import math
from qntsim.kernel.quantum_kernel import KetState
import random
import logging
logger = logging.getLogger("main_logger.application_layer." + "e91")


_psi_minus = [complex(0) , complex(math.sqrt(1 / 2)), -complex(math.sqrt(1 / 2)), complex(0)]


class E91():

    # Request transport manager  for entanglements
    def request_entanglements(self,sender,receiver,n):
        sender.transport_manager.request(receiver.owner.name,3e12,n,20e12,0,.7,5e12)
        source_node_list=[sender.name]
        return sender,receiver,source_node_list
    

    # Sets the sender and receiver as alice and bob respectively, and request entanglements 
    def roles(self,alice,bob,n):
        sender=alice
        receiver=bob
        print('sender, receiver',sender.owner.name,receiver.owner.name)
        logger.info('sender, receiver are '+sender.owner.name+" "+receiver.owner.name)
        return self.request_entanglements(sender,receiver,n)

    # circuit measurements
    def measurement(self,qm,choice, key):
        if choice == 1: 
            Circuit=BaseCircuit.create("Qutip")      #X observable
            circ=Circuit(1)
            circ.h(0)
            circ.measure(0)
            output=qm.run_circuit(circ,[key])

        if choice == 2:  
            Circuit=BaseCircuit.create("Qutip")       #W observable
            circ=Circuit(1)
            circ.s(0)
            # circ.
            circ.h(0)
            circ.t(0)
            circ.h(0)
            circ.measure(0)
            output=qm.run_circuit(circ,[key])

        if choice == 3:  
            Circuit=BaseCircuit.create("Qutip")       #Z observable
            circ=Circuit(1)
            circ.measure(0)
            output=qm.run_circuit(circ,[key])

        if choice == 4: 
            Circuit=BaseCircuit.create("Qutip")        #V observable
            circ=Circuit(1)
            circ.s(0)
            circ.h(0)
            print(circ)
            circ.tdg(0)
            circ.h(0)
            circ.measure(0)
            output=qm.run_circuit(circ,[key])
        
        return output
    
   
    ###Set  entangled state to psi_minus 
    ###TODO: Unitary Operations to change state instead of hard coding value

    def set_state_psi_minus(self , alice ,bob) :  
        
        qm_alice=alice.timeline.quantum_manager
        qm_bob=bob.timeline.quantum_manager
        bob_entangled_key=[] ##Entangled states of Bob Nodes
        alice_bob_map={}  ### Bob key<---->Alice key Map of entanglement
        
        for info in bob.resource_manager.memory_manager:
            
            if info.state=='ENTANGLED':

                key=info.memory.qstate_key
                state0=qm_bob.get(key) 
                
                ##Update bob's state in all keys associated with the state at bob node
                for key1 in state0.keys:
                    qm_bob.states[key1].state = _psi_minus
                
                bob_entangled_key.append(key) 
        

        for info in alice.resource_manager.memory_manager:
            if info.state=='ENTANGLED':
                
                key=info.memory.qstate_key
                state0=qm_alice.get(key) 
               
                ##Update alice's state in all keys associated with the state at alice node
                for key1 in state0.keys:
                    qm_alice.states[key1].state = _psi_minus
                    if key1!=key :
                        alice_bob_map[key1]=key          

        return alice,bob,alice_bob_map,bob_entangled_key


    ### Alice measurement of entangled qubits
    def alice_measurement(self,alice):
        choice=[1,2,3]
        qm_alice=alice.timeline.quantum_manager
        meas_results_alice={} ###entangled key <---> measure result at that qubit MAP
        alice_choice_list={} ###entangled key <---> Random Basis Choice of Alice MAP

        for info in alice.resource_manager.memory_manager:
            if info.state=='ENTANGLED':
                
                key=info.memory.qstate_key 
                state1=qm_alice.get(key)
                
                ##Alice Random Basis Choice and measure result for a particular entangled qubit
                alice_choice=random.randint(1, 3)
                meas_results_alice[key]=self.measurement(qm_alice,alice_choice,key)
                alice_choice_list[key]=alice_choice
        
        return alice_choice_list,meas_results_alice

   
    ### Bob measurement of entangled qubits
    def bob_measurement(self,bob,bob_entangled_key):
        choice=[2,3,4]
        qm_bob=bob.timeline.quantum_manager
        meas_results_bob={} ###entangled key <---> measure result at that qubit: MAP
        bob_choice_list={} ###entangled key <---> Random Basis Choice of Bob :MAP
          
        for info in bob.resource_manager.memory_manager:
            
            key=info.memory.qstate_key
            state0=qm_bob.get(key) 

            ##Bob Random Basis Choice and measure result for a particular entangled qubit
            if key in bob_entangled_key:
                bob_choice=random.randint(2, 4)
                meas_results_bob[key]=self.measurement(qm_bob,bob_choice,key)
                bob_choice_list[key]=bob_choice
        return bob_choice_list,meas_results_bob

    

    ### ACTION OF EVE:
        ##Eve has access to both Alice Qubit or Bob Qubit Or Both Qubits( Hence have access to the node's quantum memory information)
            #Eve detects/measures those Qubits 
            #where alice and bob doesnt have knowledge of eve's presence  
            #Hence ALice and Bob Continues to measure the qubits     
    def eve_measurement(self,alice,bob,alice_bob_map,bob_entangled_key):
               # eveMeasurementChoices = []

        

        choice=[2,3] ### These basis choices are involved in Secret key detection
        qm_alice=alice.timeline.quantum_manager
        qm_bob=bob.timeline.quantum_manager
        eve_meas_results_alice={} ##Eve measurement of Alice side Qubit
        eve_alice_choice_list={}  ## Random Basis Choice for Above
        eve_meas_results_bob={} ##Eve measurement of Bob side Qubit
        eve_bob_choice_list={}  ##Random Basis Choice for Above

        

        for bob_key in bob_entangled_key:
            alice_key=alice_bob_map[bob_key]
            if random.uniform(0, 1) <= 0.5:
                eve_alice_choice_list[alice_key]=2
                eve_bob_choice_list[bob_key]=2
            else:
                eve_alice_choice_list[alice_key]=3
                eve_bob_choice_list[bob_key]=3
          
        
        for info in alice.resource_manager.memory_manager:  
            if info.state=='ENTANGLED': 
                key=info.memory.qstate_key 
                eve_alice_choice= eve_alice_choice_list[key]
                eve_meas_results_alice[key]=self.measurement(qm_alice,eve_alice_choice,key)
                
       
        for info in bob.resource_manager.memory_manager:
            key=info.memory.qstate_key
            if key in bob_entangled_key:
                eve_bob_choice= eve_bob_choice_list[key]
                eve_meas_results_bob[key]=self.measurement(qm_bob,eve_bob_choice,key)
               
       
        return eve_meas_results_alice,eve_alice_choice_list,eve_meas_results_bob,eve_bob_choice_list
        
    
    def chsh_correlation(self,alice_meas,bob_meas,alice_choice,bob_choice,bob_entangled_key,alice_bob_map):

        countA1B2=[0,0,0,0]
        countA1B4=[0,0,0,0]
        countA3B2=[0,0,0,0]
        countA3B4=[0,0,0,0]
        check_list = ['00','01','10','11']
        res=[]

        for bob_key in bob_entangled_key:

            bob_meas_i=list(bob_meas[bob_key].items())
            alice_key=alice_bob_map[bob_key]
            alice_meas_i=list(alice_meas[alice_key].items())

            res2=str(alice_meas_i[0][1])+str(bob_meas_i[0][1])
           
            if (alice_choice[alice_key]==1 and bob_choice[bob_key]==2):
                for j in range(4):
                    if res2 == check_list[j]:
                        countA1B2[j] +=1
            if (alice_choice[alice_key]==1 and bob_choice[bob_key]==4):
                for j in range(4):
                    if res2 == check_list[j]:
                        countA1B4[j] +=1

            if (alice_choice[alice_key]==3 and bob_choice[bob_key]==2):
                for j in range(4):
                    if res2 == check_list[j]:
                        countA3B2[j] +=1
            
            if (alice_choice[alice_key]==3 and bob_choice[bob_key]==4):
                for j in range(4):
                    if res2 == check_list[j]:
                        countA3B4[j] +=1

        total12=sum(countA1B2)
        total14=sum(countA1B4)
        total32=sum(countA3B2)
        total34=sum(countA3B4)

        try:
            expect12 = (countA1B2[0]-countA1B2[1]-countA1B2[2]+countA1B2[3])/total12
            expect14 = (countA1B4[0]-countA1B4[1]-countA1B4[2]+countA1B4[3])/total14
            expect32 = (countA3B2[0]-countA3B2[1]-countA3B2[2]+countA3B2[3])/total32
            expect34 = (countA3B4[0]-countA3B4[1]-countA3B4[2]+countA3B4[3])/total34
            corr=expect12-expect14+expect32+expect34

            return corr
        except ZeroDivisionError:
            print(f'Error occured,Retry e91 again')
            return 0


    ####TODO: Generalise Eve's Access to qubits
                ## All entangled qubits /only few entangled qubits
                ## Only Alice or bob or Both
    def eve_run(self,alice,bob,n):

        alice,bob,alice_bob_map,bob_entangled_key=self.set_state_psi_minus(alice,bob)

        eve_meas_alice,eve_alice_choice_list,eve_meas_bob,eve_bob_choice_list=self.eve_measurement(alice,bob,alice_bob_map, bob_entangled_key)

        alice_choice,alice_meas=self.alice_measurement(alice)

        bob_choice,bob_meas=self.bob_measurement(bob,bob_entangled_key)

        key_mismatch=0

        alicechoice , bobchoice ,evealicechoice ,evebobchoice = [],[] ,[],[]
        aliceresults ,bobresults ,evealiceresults ,evebobresults = [],[] ,[],[]
   
        alice_keyl, bob_keyl,eve_keyl=[],[],[] ###Alice , Bob ,Eve Key List
        alice_results,bob_results,eve_alice_results,eve_bob_results ={},{},{},{} ### Qubit Key <---> Meas results MAPs

        for bob_key in bob_entangled_key:
           
            bob_meas_i=list(bob_meas[bob_key].items())
            alice_key=alice_bob_map[bob_key]
            alice_meas_i=list(alice_meas[alice_key].items())
            eve_meas_bob_i=list(eve_meas_bob[bob_key].items())
            eve_meas_alice_i=list(eve_meas_alice[alice_key].items())

            if alice_meas_i[0][1]==0 and bob_meas_i[0][1] ==0:
                alice_results[alice_key]=-1 
                bob_results[bob_key]=-1

            if alice_meas_i[0][1]==0 and bob_meas_i[0][1] ==1:
                alice_results[alice_key]=1 
                bob_results[bob_key]=-1

            if alice_meas_i[0][1]==1 and bob_meas_i[0][1] ==0:
                alice_results[alice_key]=-1 
                bob_results[bob_key]=1

            if alice_meas_i[0][1]==1 and bob_meas_i[0][1] ==1:
                alice_results[alice_key]=1  
                bob_results[bob_key]=1
            
            if eve_meas_alice_i[0][1]==0 and eve_meas_bob_i[0][1] ==0:
                eve_alice_results[alice_key]=-1 
                eve_bob_results[bob_key]=-1
                
            if eve_meas_alice_i[0][1]==0 and eve_meas_bob_i[0][1] ==1:
                eve_alice_results[alice_key]=1 
                eve_bob_results[bob_key]=-1
                
            if eve_meas_alice_i[0][1]==1 and eve_meas_bob_i[0][1] ==0:
                eve_alice_results[alice_key]=-1 
                eve_bob_results[bob_key]=1
                
            if eve_meas_alice_i[0][1]==1 and eve_meas_bob_i[0][1] ==1:
                eve_alice_results[alice_key]=1 
                eve_bob_results[bob_key]=1
                

            if (alice_choice[alice_key]==2 and bob_choice[bob_key]==2) or (alice_choice[alice_key]==3 and bob_choice[bob_key]==3):
                print('Base match',alice_meas[alice_key],bob_meas[bob_key])
                eve_keyl.append([str(eve_alice_results[alice_key]),str(eve_bob_results[bob_key])])
                alice_keyl.append(str(alice_results[alice_key]))
                bob_keyl.append(str(-bob_results[bob_key]))
                
            alicechoice.append(str(alice_choice[alice_key]))
            aliceresults.append(str(alice_results[alice_key]))
            bobchoice.append(str(bob_choice[bob_key]))
            bobresults.append(str(bob_results[bob_key]))
            evealicechoice.append(str(eve_alice_choice_list[alice_key]))
            evebobchoice.append(str(eve_bob_choice_list[bob_key]))
            evealiceresults.append(str(eve_alice_results[alice_key]))
            evebobresults.append(str(eve_bob_results[bob_key]))
            
            alicechoice= list(map(lambda x: x.replace('1', 'X'), alicechoice))
            alicechoice= list(map(lambda x: x.replace('2', 'W'), alicechoice))
            alicechoice= list(map(lambda x: x.replace('3', 'Z'), alicechoice))
            alicechoice= list(map(lambda x: x.replace('4', 'V'), alicechoice))
            aliceresults= list(map(lambda x: x.replace('-1', '0'), aliceresults))
            alice_keyl= list(map(lambda x: x.replace('-1', '0'), alice_keyl))
           
           
            bobchoice= list(map(lambda x: x.replace('1', 'X'), bobchoice))
            bobchoice= list(map(lambda x: x.replace('2', 'W'), bobchoice))
            bobchoice= list(map(lambda x: x.replace('3', 'Z'), bobchoice))
            bobchoice= list(map(lambda x: x.replace('4', 'V'), bobchoice))
            bobresults= list(map(lambda x: x.replace('-1', '0'), bobresults))
            bob_keyl= list(map(lambda x: x.replace('-1', '0'), bob_keyl))


            evealicechoice= list(map(lambda x: x.replace('1', 'X'), evealicechoice))
            evealicechoice= list(map(lambda x: x.replace('2', 'W'), evealicechoice))
            evealicechoice= list(map(lambda x: x.replace('3', 'Z'), evealicechoice))
            evealicechoice= list(map(lambda x: x.replace('4', 'V'), evealicechoice))
            evealiceresults= list(map(lambda x: x.replace('-1', '0'),evealiceresults))

            evebobchoice= list(map(lambda x: x.replace('1', 'X'), evebobchoice))
            evebobchoice= list(map(lambda x: x.replace('2', 'W'), evebobchoice))
            evebobchoice= list(map(lambda x: x.replace('3', 'Z'), evebobchoice))
            evebobchoice= list(map(lambda x: x.replace('4', 'V'), evebobchoice))
            evebobresults= list(map(lambda x: x.replace('-1', '0'),evebobresults))
        
        key_error=0

        if len(alice_keyl)!=0:
            checkKeyIndexl=random.sample(range(1, len(alice_keyl)), math.ceil(0.2*len(alice_keyl)))
            for j in checkKeyIndexl:
                if alice_keyl[j] != bob_keyl[j]:
                    key_error= key_error+1
            test_error_rate=key_error/len(checkKeyIndexl)
                
            keyLength=len(alice_keyl)
            abKeyMismatches = 0 # number of mismatching bits in the keys of Alice and Bob
            eaKeyMismatches = 0 # number of mismatching bits in the keys of Eve and Alice
            ebKeyMismatches = 0 # number of mismatching bits in the keys of Eve and Bob

            for j in range(len(alice_keyl)):
                if alice_keyl[j] != bob_keyl[j]:
                    abKeyMismatches += 1
                if eve_keyl[j][0]!= alice_keyl[j]:
                    eaKeyMismatches += 1
                if eve_keyl[j][1]!= bob_keyl[j]:
                    ebKeyMismatches +=1

                
            eaKnowledge = (keyLength - eaKeyMismatches)/keyLength # Eve's knowledge of Alice's key
            ebKnowledge = (keyLength - ebKeyMismatches)/keyLength

            error_rate=abKeyMismatches/len(alice_keyl)
                
            print('Alice keys', alice_keyl)
            print('Bob keys', bob_keyl)
            print('Eve keys',eve_keyl)
            print('Key length',len(alice_keyl))
            print('ab Mismatched keys', abKeyMismatches)
            print('ab check key error',key_error)
            print('Eve\'s knowledge of Alice\'s key: ' + str(round(eaKnowledge * 100, 2)) + ' %')
            print('Eve\'s knowledge of Bob\'s key: ' + str(round(ebKnowledge * 100, 2)) + ' %')  
            chsh_value=self.chsh_correlation(alice_meas,bob_meas,alice_choice,bob_choice,bob_entangled_key,alice_bob_map)
            print('Correlation value', chsh_value, round(chsh_value,2))
            

            res = {
                "sender_basis_list":alicechoice,
                "sender_meas_list":aliceresults,
                "eve_sender_basis_list":evealicechoice,
                "eve_sender_meas_list":evealiceresults,
                "receiver_basis_list":bobchoice,
                "receiver_meas_list":bobresults,
                "eve_receiver_basis_list":evebobchoice,
                "eve_receiver_meas_list":evebobresults,
                "sender_keys": alice_keyl,
                "receiver_keys": bob_keyl,
                "keyLength": len(alice_keyl),
                'keymismatch': abKeyMismatches,
                'Error_rate': error_rate,
                'Testkeylength':math.ceil(0.2*len(alice_keyl)),
                'Testkeymismatch':key_error,
                'Testerror_rate':test_error_rate,
                'correlation': str(round(chsh_value,3)),
                'Success':True
            }
            #print(res)
            return res
        else :

            res = {
                "sender_basis_list":alicechoice,
                "sender_meas_list":aliceresults,
                "eve_sender_basis_list":evealicechoice,
                "eve_sender_meas_list":evealiceresults,
                "receiver_basis_list":bobchoice,
                "receiver_meas_list":bobresults,
                "eve_receiver_basis_list":evebobchoice,
                "eve_receiver_meas_list":evebobresults,
                "sender_keys": alice_keyl,
                "receiver_keys": bob_keyl,
                "keyLength": len(alice_keyl),
                "Success":False   
            }
            return res
            


    def run(self,alice,bob,n):

        alice,bob,alice_bob_map,bob_entangled_key=self.set_state_psi_minus(alice,bob)
        alice_choice,alice_meas=self.alice_measurement(alice)
        bob_choice,bob_meas=self.bob_measurement(bob,bob_entangled_key)
        key_mismatch=0
        alice_keyl,bob_keyl=[],[]
        alice_results, bob_results ={},{}
        alicechoice , bobchoice = [],[]
        aliceresults ,bobresults = [],[]

        print('Alice Measurements',alice_meas)
        print('Alice choice',alice_choice)
        print('Bob Measuremenst', bob_meas)
        print('Bob choice',bob_choice)
        print(bob_entangled_key)
        print("e91 check",n)

        
        
        for bob_key in bob_entangled_key:

            
            
            bob_meas_i=list(bob_meas[bob_key].items())
            alice_key=alice_bob_map[bob_key]
            alice_meas_i=list(alice_meas[alice_key].items())

            if alice_meas_i[0][1]==0 and bob_meas_i[0][1] ==0:
                alice_results[alice_key]=-1 
                bob_results[bob_key]=-1
            elif alice_meas_i[0][1]==0 and bob_meas_i[0][1] ==1:
                alice_results[alice_key]=1 
                bob_results[bob_key]=-1
            elif alice_meas_i[0][1]==1 and bob_meas_i[0][1] ==0:
                alice_results[alice_key]=-1 
                bob_results[bob_key]=1
            elif alice_meas_i[0][1]==1 and bob_meas_i[0][1] ==1:
                alice_results[alice_key]=1  
                bob_results[bob_key]=1
            
            if (alice_choice[alice_key]==2 and bob_choice[bob_key]==2) or (alice_choice[alice_key]==3 and bob_choice[bob_key]==3):
                print('Base match',alice_meas[alice_key],bob_meas[bob_key])
                alice_keyl.append(str(alice_results[alice_key]))
                bob_keyl.append(str(-bob_results[bob_key]))
                
            alicechoice.append(str(alice_choice[alice_key]))
            aliceresults.append(str(alice_results[alice_key]))
            bobchoice.append(str(bob_choice[bob_key]))
            bobresults.append(str(bob_results[bob_key]))
            
            alicechoice= list(map(lambda x: x.replace('1', 'X'), alicechoice))
            alicechoice= list(map(lambda x: x.replace('2', 'W'), alicechoice))
            alicechoice= list(map(lambda x: x.replace('3', 'Z'), alicechoice))
            alicechoice= list(map(lambda x: x.replace('4', 'V'), alicechoice))
            aliceresults= list(map(lambda x: x.replace('-1', '0'), aliceresults))
            alice_keyl= list(map(lambda x: x.replace('-1', '0'), alice_keyl))
           
           
            bobchoice= list(map(lambda x: x.replace('1', 'X'), bobchoice))
            bobchoice= list(map(lambda x: x.replace('2', 'W'), bobchoice))
            bobchoice= list(map(lambda x: x.replace('3', 'Z'), bobchoice))
            bobchoice= list(map(lambda x: x.replace('4', 'V'), bobchoice))
            bobresults= list(map(lambda x: x.replace('-1', '0'), bobresults))
            bob_keyl= list(map(lambda x: x.replace('-1', '0'), bob_keyl))
           
        for j in range(len(alice_keyl)):
            if alice_keyl[j] != bob_keyl[j]:
                key_mismatch += 1
       
        print('Alice keys', alice_keyl)
        print('Bob keys', bob_keyl)
        print('Alice res', alice_results)
        print('Bob res', bob_results)
        print('Mismatched keys', key_mismatch)
        chsh_value=self.chsh_correlation(alice_meas,bob_meas,alice_choice,bob_choice,bob_entangled_key,alice_bob_map)
        print('Correlation value', chsh_value, round(chsh_value,3))
        error_rate=key_mismatch/len(alice_keyl)

        key_error=0
        if len(alice_keyl)!=0:
            checkKeyIndexl=random.sample(range(1, len(alice_keyl)), math.ceil(0.2*len(alice_keyl)))
            for j in checkKeyIndexl:
                if alice_keyl[j] != bob_keyl[j]:
                    key_error= key_error+1
            test_error_rate=key_error/len(checkKeyIndexl)

            res = {
                "sender_basis_list":alicechoice,
                "sender_meas_list":aliceresults,
                "receiver_basis_list":bobchoice,
                "receiver_meas_list":bobresults,
                "sender_keys": alice_keyl,
                "receiver_keys": bob_keyl,
                "keyLength": len(alice_keyl),
                'keymismatch': key_mismatch,
                'Error_rate': error_rate,
                'Testkeylength':math.ceil(0.2*len(alice_keyl)),
                'Testkeymismatch':key_error,
                'Testerror_rate':test_error_rate,
                'correlation': str(round(chsh_value,3)),
                'Success':True
            }    
            print(res)
            return res

        else:

            res = {
                "sender_basis_list":alicechoice,
                "sender_meas_list":aliceresults,
                "receiver_basis_list":bobchoice,
                "receiver_meas_list":bobresults,
                "sender_keys": alice_keyl,
                "receiver_keys": bob_keyl,
                "keyLength": len(alice_keyl),
                'keymismatch': key_mismatch,
                'Success':False
            }
            
        
###############################################################################################

# sender and receiver (Type : String)-nodes in network 
# backend (Type : String) -Qiskit
# TODO: support on Qutip 
# key_length(Type : Integer ) should be <50 and >0
# virtual liks : [{"sender": a, "reveiver": b, "demand": 50}]
def set_parameters(topology):
   
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



# path (Type : String) -Path to config Json file
"""
def e91(backend,path,sender,receiver,key_length):

    trials=4
    while (trials>0):
        from qntsim.kernel.timeline import Timeline 
        Timeline.DLCZ=False
        Timeline.bk=True
        from qntsim.topology.topology import Topology
        tl = Timeline(20e12,backend)
        network_topo = Topology("network_topo", tl)
        network_topo.load_config(path)
        set_parameters(network_topo)
        if key_length==0:
            return {"Error_Msg":"key should be greater than 0.Retry Again"}

        if key_length<30 and key_length>0:
            #n=int((9*key_length)/2)
            n=int(8*key_length)
            alice=network_topo.nodes[sender]
            bob = network_topo.nodes[receiver]
            e91=E91()
            alice,bob,source_node_list=e91.roles(alice,bob,n)
            tl.init()
            tl.run()  
            res=e91.run(alice,bob,n)
            #print("res",res)
            if key_length<len(res["sender_keys"]):
                res["sender_keys"]=res["sender_keys"][:key_length]
                res["receiver_keys"]=res["receiver_keys"][:key_length] 
                res["sifted_keylength"]=key_length 
                print(res)
                return res
        trials=trials-1
    return {"Error_Msg":"Couldn't generate required length.Retry Again"}

def eve_e91(backend,path,sender,receiver,key_length):
    trials=4
    while (trials>0):
        from qntsim.kernel.timeline import Timeline 
        Timeline.DLCZ=False
        Timeline.bk=True
        from qntsim.topology.topology import Topology
        tl = Timeline(20e12,backend)
        network_topo = Topology("network_topo", tl)
        network_topo.load_config(path)
        set_parameters(network_topo)
        if key_length==0:
            return {"Error_Msg":"key should be greater than 0.Retry Again"}

        if key_length<51 and key_length>0:
            #n=int((9*key_length)/2
            n=int(8*key_length)
            alice=network_topo.nodes[sender]
            bob = network_topo.nodes[receiver]
            e91=E91()
            alice,bob,source_node_list=e91.roles(alice,bob,n)
            tl.init()
            tl.run()  
            res=e91.eve_run(alice,bob,n)
            if key_length<len(res["sender_keys"]):
                res["sender_keys"]=res["sender_keys"][:key_length]
                res["receiver_keys"]=res["receiver_keys"][:key_length] 
                res["sifted_keylength"]=key_length
                print(res) 
                return res
        trials=trials-1
    return {"Error_Msg":"Couldn't generate required length.Retry Again"}
"""
#e91("Qutip", "/home/bhanusree/Desktop/QNTv1/QNTSim-Demo/QNTSim/example/3node.json", "a", "s1", 2)

# jsonConfig (Type : Json) -Json Configuration of network 

"""
def e91(backend,jsonConfig,sender,receiver,key_length):
    from qntsim.kernel.timeline import Timeline 
    Timeline.DLCZ=False
    Timeline.bk=True
    from qntsim.topology.topology import Topology
    tl = Timeline(20e12,backend)
    network_topo = Topology("network_topo", tl)
    network_topo.load_config_json(jsonConfig)
    print(network_topo.get_virtual_graph())
    if key_length<50 and key_length>0:
        n=int((9*key_length)/2)
        alice=network_topo.nodes[sender]
        bob = network_topo.nodes[receiver]
        e91=E91()
        alice,bob=e91.roles(alice,bob,n)
        tl.init()
        tl.run()
        e91.run(alice,bob,n)
"""
"""
conf= {"nodes": [], "quantum_connections": [], "classical_connections": []}
memo = {"frequency": 2e3, "expiry": 0, "efficiency": 1, "fidelity": 1}
node1 = {"Name": "N1", "Type": "end", "noOfMemory": 50, "memory":memo}
node2 = {"Name": "N2", "Type": "end", "noOfMemory": 50, "memory":memo}
node3 = {"Name": "N3", "Type": "service", "noOfMemory": 50, "memory":memo}
conf["nodes"].append(node1)
conf["nodes"].append(node2)
conf["nodes"].append(node3)
qc1 = {"Nodes": ["N1", "N3"], "Attenuation": 1e-5, "Distance": 70}
qc2 = {"Nodes": ["N2", "N3"], "Attenuation": 1e-5, "Distance": 70}
conf["quantum_connections"].append(qc1)
conf["quantum_connections"].append(qc2)
cc11 = {"Nodes": ["N1", "N1"], "Delay": 0, "Distance": 0}
cc22 = {"Nodes": ["N2", "N2"], "Delay": 0, "Distance": 0}
cc33 = {"Nodes": ["N3", "N3"], "Delay": 0, "Distance": 0}
cc12 = {"Nodes": ["N1", "N2"], "Delay": 1e9, "Distance": 1e3}
cc13 = {"Nodes": ["N1", "N3"], "Delay": 1e9, "Distance": 1e3}
cc23 = {"Nodes": ["N2", "N3"], "Delay": 1e9, "Distance": 1e3}
cc21 = {"Nodes": ["N1", "N2"], "Delay": 1e9, "Distance": 1e3}
cc23 = {"Nodes": ["N1", "N3"], "Delay": 1e9, "Distance": 1e3}
cc32 = {"Nodes": ["N2", "N3"], "Delay": 1e9, "Distance": 1e3}
conf["classical_connections"].append(cc11)
conf["classical_connections"].append(cc22)
conf["classical_connections"].append(cc33)
conf["classical_connections"].append(cc12)
conf["classical_connections"].append(cc13)
conf["classical_connections"].append(cc23)
conf["classical_connections"].append(cc21)
conf["classical_connections"].append(cc31)
conf["classical_connections"].append(cc32)
e91("Qiskit", conf, "N1", "N2", 8)
# from qntsim.kernel.timeline import Timeline 
# Timeline.DLCZ=False
# Timeline.bk=True
# from qntsim.topology.topology import Topology
# tl1 = Timeline(20e12,"Qiskit")
# network_topo = Topology("network_topo", tl1)
# network_topo.load_config("test.json")
# print('network_topo ', network_topo.__dict__["_cc_graph"])
# print("========================================================")
# tl2 = Timeline(20e12,"Qiskit")
# network_topo_json = Topology("network_topo_json", tl2)
# network_topo_json.load_config_json(conf)
# print('network_topo_json ',network_topo_json.__dict__["_cc_graph"])
"""

#conf={'nodes': [{'Name': 'n1', 'Type': 'end', 'noOfMemory': 500, 'memory': {'frequency': 2000, 'expiry': 2000, 'efficiency': 0, 'fidelity': 0.93}}, {'Name': 'n2', 'Type': 'service', 'noOfMemory': 500, 'memory': {'frequency': 2000, 'expiry': 2000, 'efficiency': 0, 'fidelity': 0.93}}], 'quantum_connections': [{'Nodes': ['n1', 'n2'], 'Attenuation': 1e-05, 'Distance': 70}], 'classical_connections': [{'Nodes': ['n1', 'n1'], 'Delay': 0, 'Distance': 1000}, {'Nodes': ['n1', 'n2'], 'Delay': 1000000000, 'Distance': 1000}, {'Nodes': ['n2', 'n1'], 'Delay': 1000000000, 'Distance': 1000}, {'Nodes': ['n2', 'n2'], 'Delay': 0, 'Distance': 1000}]}
#e91("Qiskit", conf, "n1", "n2", 8)


"""
    def alice_measurement(self,alice,bob):
        choice=[1,2,3]
        qm_alice=alice.timeline.quantum_manager
        qm_bob=bob.timeline.quantum_manager
        meas_results_alice={}
        alice_choice_list={}
        bob_entangled_key=[]
        alice_bob_map={}
        
        
        for info in bob.resource_manager.memory_manager:
            if info.state=='ENTANGLED':
                
                key=info.memory.qstate_key
                state0=qm_bob.get(key) 
                print('bob initial state ', key ,state0 )
                
                for key1 in state0.keys:
                    qm_bob.states[key1].state = _psi_minus
                
                state1=qm_bob.get(key)
                print('initial state1 ',state1)
                bob_entangled_key.append(key) 
        
        for info in alice.resource_manager.memory_manager:
            if info.state=='ENTANGLED':
                
                key=info.memory.qstate_key
                state0=qm_alice.get(key) 
                print('alice initial state ',key,state0)
                
                for key1 in state0.keys:
                    qm_alice.states[key1].state = _psi_minus
                    if key1!=key :
                        alice_bob_map[key1]=key
                
                state1=qm_alice.get(key)
                print('initial state1 ',state1)
        
                alice_choice=random.randint(1, 3)
                
                #outputa=self.measurement(qm_alice,alice_choice,key)
                #meas_results_alice.append((key,self.measurement(qm_alice,alice_choice,key)))
                #alice_choice_list.append((key,alice_choice))
                meas_results_alice[key]=self.measurement(qm_alice,alice_choice,key)
                alice_choice_list[key]=alice_choice
        # print('Alice measuremnt reuslts',meas_results_alice)
        return alice_bob_map,bob_entangled_key,alice_choice_list,meas_results_alice
    
    #measurements on bob side
    def bob_measurement(self,bob,bob_entangled_key):
        qm_bob=bob.timeline.quantum_manager
        meas_results_bob={}
        bob_choice_list={}
        choice=[2,3,4]
        
        for info in bob.resource_manager.memory_manager:
            
            key=info.memory.qstate_key
            state0=qm_bob.get(key) 
            print('bob initial state ',state0)
            #print("check",qm_alice.states[key])
            #qm_bob.states[key].state = _psi_minus
            #state1=qm_bob.get(key)
            #print('bob initial state1 ',state1)
            if key in bob_entangled_key:
                bob_choice=random.randint(2, 4)
                #print('keys bob',key)
                #outputb=self.measurement(qm_bob,bob_choice,key)
                meas_results_bob[key]=self.measurement(qm_bob,bob_choice,key)
                bob_choice_list[key]=bob_choice
        return bob_choice_list,meas_results_bob
    """