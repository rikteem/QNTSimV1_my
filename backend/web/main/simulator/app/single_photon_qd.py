from random import choices
import random
from qntsim.kernel.timeline import Timeline
Timeline.DLCZ=False
Timeline.bk=True
from qntsim.topology.topology import Topology
from qntsim.components.circuit import QutipCircuit
import numpy as np
from numpy.random import randint
from qiskit import *


class SinglePhotonQD():
    
    
    def request_entanglements(self,sender,receiver,n):
        sender.transport_manager.request(receiver.owner.name,5e12,n,20e12,0,.5,5e12)
        source_node_list=[sender.name]
        return sender,receiver,source_node_list

    def roles(self,alice,bob,n):
        sender=alice
        receiver=bob
        print('sender, receiver',sender.owner.name,receiver.owner.name)    
        return self.request_entanglements(sender,receiver,n)
    
    
    def bob_encodes(self, message="0010", N=5):
        """
        Method to encode the message into the photons based on the protocol by Ji and Zhang
        
        Parameters:
        message : str
            Bit string to be teleported through the photons
        N : int
            Number of photons in each batch
        
        Returns:
        initials : list
            List of the intial states of the photon
        circuits : list
            List of <QuantumCircuit> objects, each representing the N photons in a
            batch
        """
        print('Bob encodes')
        initials, circuits = [], []
        msg_len = len(message)
        for i in range(N):
            initial = randint(4, size=msg_len)
            qc = QuantumCircuit(msg_len, msg_len)
            for i in range(msg_len):
                ini = initial[i]
                if ini%2==1:
                    qc.x(i)
                if int(ini/2)==1:
                    qc.h(i)
                msg = message[i]
                if msg==1 or msg=='1':
                    qc.x(i)
                    qc.z(i)
            initials.append(initial.tolist())
            circuits.append(qc)
        
        return initials, circuits


    # ## Alice checks for eavesdropper
    # 
    # Alice randomly selects N-1 batches and measures each photon in the z or the x basis randomly. Then based on the measurement outcomes and the bases she chose, it is possible to calculate the error accumulated in the protocol. If the error surpasses the threshold, the protocol is discarded.
    # 
    # This function takes the list of initials and circuits as an input, and returns 'True' or 'False' based on the threshold check, with the remaining circuit and its initial_states.
    # 
    # (Note:- The code block still doesn't include the error checking part)

    # In[3]:


    def alice_checks(self,initials, circuits, device="aer_simulator"):
        """
        Method to check for an eavesdropper in the channels
        
        Parameters:
        initials : list
            list of initial states of the photons
        circuits : list
            list of <QuantumCircuit> objects, representing the photons
        (optional) device : str
            The device on which the <QuantumCircuit> are to be executed
        
        Returns:
        initial : int
            The initial state of the single photon in the batch used for communication
        circuit : <QuantumCircuit>
            The <QuantumCircuit> object representing the single photon
        initials : list
            List of the intial states of the photons used for performing checks
        bases : list
            List of bases {z, x} along which the remaining photons were measured
        counts : list
            List of the measurement outcomes of these photons used for check
        """
        
        index = randint(len(circuits))
        initial = initials.pop(index)
        circuit = circuits.pop(index)
        bases = []
        for circ in circuits:
            base = randint(2, size=circ.num_qubits)
            #print(bases)
            circ.barrier()
            for i in range(circ.num_qubits):
                if base[i]==1:
                    circ.h(i)
            circ.barrier()
            circ.measure(range(circ.num_qubits), range(circ.num_qubits))
            #print(circ)
            bases.append(base)
        backend = Aer.get_backend(device)
        result = execute(circuits, backend=backend, shots=1).result()
        counts = []
        for circ in circuits:
            counts.append(list(result.get_counts(circ))[0])
        
        return initial, circuit, initials, bases, counts, 


    # ## Bob estimates the fidelity of the channels
    # 
    # After receiving the list of the position, bases and measurement outcomes from Alice, Bob uses these information with his own message to determine the fidelity of the channels, which further helps in detecting the presence of any eavesdropper.
    # 
    # The function takes initials, message, bases, counts as inputs and prints the fidelity of each of the batch of photons, Alice has chosen for detection. The function, by default, returns 'True' which can be later be modified to take into account any threshold provided by the user.

    # In[4]:


    def bob_determines(self,initials, message, bases, counts):
        """
        Method to estimate the fidelity of the channels
        
        Parameters:
        initials : list
            list of the initial states of the checking photons
        message : str
            Bit string, teleported through the photons, used in this case to
            estimate the fidelity of the channels
        bases : list
            List of bases {z, x} along which the remaining photons were measured
        counts : list
            List of the measurement outcomes of these photons used for check
        
        Returns:
        (constant) True : bool
            The function, for now, returns a constant 'True' value, which can be
            later replaced by the threshold condition for the channels
        """
        
        fidelity = 0
        b = 0
        for i in range(len(initials)):
            initial = initials[i]
            base = bases[i]
            count = counts[i]
            for j in range(len(initial)):
                ini = initial[j]
                msg = message[j]
                bse = base[j]
                cnt = count[j]
                if bse==1==int(ini/2):
                    b+=1
                    if ini%2==int(msg)!=bse!=int(cnt):
                        fidelity+=1
        print("fidelity = ", fidelity/b)
        
        return True


    # ## Alice encodes her message
    # 
    # Upon checking and not finding any eavesdropper, Alice encodes her message on the remaining batch of photons, and then measures them based on the initial_states of these photons. She then decodes Bob's message based on the initial_states and the measurement outcome, thus recovering Bob's message and, publicly announces her measurement outcomes for Bob to decode her message.
    # 
    # The function takes the remaining circuit and its initial_states as input with Alice's message, and returns the measurement outcome of the circuit.

    # In[5]:


    def alice_encodes(self,initial, circuit, message="0100", device="aer_simulator"):
        """
        Method to encode the second message into the photon chosen for
        communication and, also decode the message send by the first party
        
        Parameters:
        initial : int
            The initial state of the photon used for communication
        circuit : <QuantumCircuit>
            The circuit representing the communicating photon
        message : str
            The bit string of the second message that needs to be conveyed
        (optional) device : str
            The device on which the <QuantumCircuit> is to be executed
        
        Returns:
        measure : int
            The measured outcome of the photon
        string : str
            The bit string of the first message
        """
        
        #initial = initials[index]
        circuit.barrier()
        for i in range(len(message)):
            msg = message[i]
            if msg==1 or msg=='1':
                circuit.x(i)
                circuit.z(i)
            ini = initial[i]
            if int(ini/2)==1:
                circuit.h(i)
            if ini%2==1:
                circuit.x(i)
        circuit.barrier()
        circuit.measure(range(circuit.num_qubits), range(circuit.num_qubits-1, -1, -1))
        backend = Aer.get_backend(device)
        result = execute(circuit, backend=backend, shots=1).result()
        counts = result.get_counts(circuit)
        measure = list(list(counts)[0])
        message = list(message)
        string = ''.join(str(int(measure[i]!=message[i])) for i in range(len(measure)))
        '''
        for i in range(len(measure)):
            string = string+str(int(measure[i]!=message[i]))
        #print("Alice decoded:", string)
        '''
        
        return measure, string


    # ## Bob decodes Alice's message
    # 
    # Hearing the measurement outcome from Alice, Bob uses the information and his message to decode Alice's message.

    # In[6]:


    def bob_decodes(self,measure, message="0010"):
        """
        Method to decode the second message from the measurement outcome and the
        first message
        
        Parameters:
        measure : int
            The measured outcome of the photon
        message : str
            The bit string of the first message, used for decoding the second message
        
        Returns:
        string : str
            The bit string of the second message
        """
        
        message = list(message)
        string = ''.join(str(int(measure[i]!=message[i])) for i in range(len(measure)))
        '''
        for i in range(len(measure)):
            string = string+str(int(measure[i]!=message[i]))
        #print("Alice decoded:", string)
        '''
        
        return string

    
    
    def run(self, alice, bob, message1, message2, attack):
        
        msg1, msg2 = [],[]
        for i in message1:
            msg1.append(bin(ord(i))[2:])
        for i in message2:
            msg2.append(bin(ord(i))[2:])
        
        string1, string2 = [],[]
        # print('messages', n, msg1,msg2)
        n=5
        for i in range(len(msg1)):
            print('message', msg1[i])
            initials, circuits = self.bob_encodes(message = msg1[i], N=n)
            if attack:
                for circ in circuits:
                    circ.barrier()
                    circ.measure(range(circ.num_qubits), range(circ.num_qubits))
            initial, circuit, initials, bases, counts = self.alice_checks(initials, circuits)
            if self.bob_determines(initials, msg1[i], bases, counts):
                measure, str1 = self.alice_encodes(initial=initial, circuit=circuit, message=msg2[i])
                str2 = self.bob_decodes(measure, message=msg1[i])
            else:
                print("Transmission compromised")
                break
            string1.append(str1)
            string2.append(str2)
            #print(str1, str2)
        string1 = ''.join(chr(int(string, 2)) for string in string1)
        string2 = ''.join(chr(int(string, 2)) for string in string2)
        print("Receiver decodes: ", string1)
        print("Sender decodes: ", string2)
        error=0
        res ={
            "input_message1": message1,
            "input_message2" : message2,
            "attack" : attack,
            "output_message1" : string1,
            "output_message2" : string2,
            "error" : error
                
        }
        print("result",res)
        return res