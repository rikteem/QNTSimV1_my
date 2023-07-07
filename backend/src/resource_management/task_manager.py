import itertools
import logging
import os
import traceback
from logging import config

from qntsim.conf import LOG_CONFIG_FILE

print(__name__,LOG_CONFIG_FILE,os.getcwd())
config.fileConfig(LOG_CONFIG_FILE)
#from qntsim.utils.log import logger

from typing import TYPE_CHECKING, Callable, List, Tuple

if TYPE_CHECKING:
    from ..entanglement_management.entanglement_protocol import \
        EntanglementProtocol
    from ..network_management.request import Request
    from ..network_management.reservation import Reservation
    from ..protocol import Protocol
    from ..topology.node import QuantumRouter
    from .memory_manager import MemoryInfo, MemoryManager
    from .resource_manager import ResourceManager

class Task:
	id_counter = itertools.count()

	"""
		dependencies: list of Tasks that are needed by current task
	"""
	def __init__(self, name, dependencies, timestamp, loops, action: Callable[
                     [List["MemoryInfo"]], Tuple["Protocol", List["str"], List[Callable[["Protocol"], bool]]]], task_manager, **kwargs):
		self.id = next(self.id_counter)
		self.name = name
		self.status = 'created'
		self.dependencies = dependencies
		self.action = action
		#print(f'type(self.action) : {type(action)}')
		#print(f'action:   {self.action}')
		self.creation_time = timestamp
		self.updation_time = ''   #start execution time
		self.completion_time = ''
		self.task_manager = task_manager
		self.memories_info = []
		if 'memories_info' in kwargs:
			self.memories_info = kwargs['memories_info']
		if 'mem_indices' in kwargs:
			mem_indices = kwargs['mem_indices']
			for mem_index in mem_indices:
				self.memories_info.append(self.task_manager.owner.resource_manager.memory_manager.__getitem__(mem_index))
		self.subtasks = []
		self.dependencies_subtask_map = {}
		#self.memory_to_subtask = {} #only used to find generation subtask from memory_info
		self.other_node = None
		self.is_vl_final_swap_task= False
		self.has_already_run = False
		self.can_run_on_init = False
		self.loops = loops

	def wait(self):
		self.status = 'waiting'

	def wakeup(self, timestamp):
		self.status = 'running'
		self.updation_time = timestamp
		#return self.action, self.args

	#We can also experiment with callbacks here to provide custom run() method to each task
	def run(self, ):
		#If there are no dependencies for the task
			#Pick memory from the 
			#Run all of the subtasks
		#If there are dependencies for the task and since run is called, one has been met
			#Pick from the subtask pool and Find an instance of the subtask that is availble and start running it
		pass

	def set_reservation(self, reservation: "Request") -> None:
		self.reservation = reservation
	
	def get_reservation(self) -> "Request":
		return self.reservation

	def on_subtask_success(self, subtask):
		#Convey this info to the task manager and store the args in task manager
		#print('########Subtask Succeeded############## subtask.protocol name', subtask.name)
		self.task_manager.subtask_success(subtask)
	
	def on_subtask_failure(self, subtask):
		#Convey this info to the task manager and store the args in task manager
		#print(f'########Subtask Failed############## : {subtask.name}')
		self.task_manager.subtask_failure(subtask)

	def init_dependency_subtask_map(self):
		for dependency in self.dependencies:
			self.dependencies_subtask_map[dependency]	= []
		#print('Initialized the dependencies_subtask_map')
		#print('current status:	', self.dependencies_subtask_map)
	
	def set_action(self, action: Callable[
                     [List["MemoryInfo"]], Tuple["Protocol", List["str"], List[Callable[["Protocol"], bool]]]]):
		self.action = action

	
	
	def set_dependency_to_subtask(self, subtask):
		subtask_list = self.dependencies_subtask_map.get(subtask.task)
		#if subtask_list == None:
		#	subtask_list = []
		subtask_list.append(subtask)
		self.dependencies_subtask_map[subtask.task] = subtask_list
		#print('Task name:	', self.name)
		#print('added a subtask to dependency  and map status is:	', [(d.name, [subt_.name for subt_ in sd]) for d, sd in self.dependencies_subtask_map.items()])

	def is_eligible(self):
		#Loop over the dependencies_subtask_map and find if a subtask of all dependencies are available
		#print('checking eligibility of:	', self.name)
		subtasks_available = []	
		subtasks_available_list = [] #append the lists
		for dependency, subtask_list in self.dependencies_subtask_map.items():
			if len(subtask_list) == 0:
				#print(f'Not eligible yet because {dependency.name} does not have an instance to allocate')
				return False, []
			subtasks_available_list.append(subtask_list)
			#subtask_list.remove(subtask_list[0])
		#subtasks_available = [subtask_list[0], subtask_list.remove(subtask_list[0])  for subtask_list in subtasks_available_list]
		for subtask_list in subtasks_available_list:
			subtasks_available.append(subtask_list[0])
			subtask_list.remove(subtask_list[0])
		#print('subtasks_available:	', [st.name for st in subtasks_available])
		return True, subtasks_available
			




class SubTask:
	def __init__(self, name,  action: Callable[
                     [List["MemoryInfo"]], Tuple["Protocol", List["str"], List[Callable[["Protocol"], bool]]]], memories_info) -> None:
		self.name = name
		self.task = None
		self.action = action
		self.dependents = []	#subtasks that depend on this
		self.dependencies = []	#subtasks that this depends on
		self.initial_dependency_subtasks = []	#list of initial subtasks that lead upto this subtask
		#self.trigger_in_any_case = [] #run these subtasks in case of both success as well as failure
		self.memories_info = memories_info		#Here we save the memory indices for which this subtask was instantiated
												#This can be a list because some subtasks like swap may need more than one memories
		#self.is_prerequisite_of = []
		self.protocols = []
		self.status = 0   # 0: not available
						  # 1: available

	"""
		Parent task upon meeting requirements runs the child subtask
		Child subtask runs the protocol encapsulated within it on the memory passed as argument to it
	"""
	def run(self):
		
		protocol, req_dsts, req_condition_funcs = self.action(self.memories_info)
		if protocol == True:
			#print('Purification not needed')
			self.on_complete(2)
			return
		
		if protocol == None:
			#print('Could not create protocol instance: ')
			self.on_complete(3)
			return 

		#print(f'task.name: {self.task.name}  for node: {self.task.task_manager.owner.name} and memory returned for this: {self.memories_info[0].index}')
		self.protocols.extend(protocol)
		protocol[0].subtask = self
		self.name = protocol[0].name	#Do something about this

		for info in self.memories_info:
			info.memory.detach(info.memory.memory_array)
			info.memory.attach(protocol[0])
		
		logging.debug('Running subtask:	' + str(self.name))
		# print('Running subtask:	' + str(self.name))
		for dst, req_func in zip(req_dsts, req_condition_funcs):
			self.task.task_manager.send_request(protocol[0], dst, req_func)
			#print('dst, req_func:	', dst, req_func)

	"""
		notify the parent task in case of success
		rerun the subtask in case of failure
	"""
	def on_complete(self, completion_status, **kwargs):
		#It will pass the memory id for which it has completed to the task_manager
		#Task manager will then run dependent task passing this memory id as argument
		if completion_status == -1:
			#Failure----We need to go back through the chain of all dependencies that lead to this point and need to retry them again
			#This has to be handled through the task manager
			#self.run()
			# print('reached inside on_complete subtask failure section')
			self.status = 0
			self.task.on_subtask_failure(self)
		elif completion_status == 1:
			#Success----Call the dependent subtask if any
			self.status = 1
			# print('reached inside on_complete subtask success with looping section')
			if self.task.loops:
				# print(f'Running the subtask again: {self.name}')
				# traceback.print_stack()
				self.run()
				return
			self.task.on_subtask_success(self)
		elif completion_status == 2:
			self.status = 1
			# print('reached inside on_complete subtask success without looping section')
			self.task.on_subtask_success(self)
		else:
			# traceback.print_stack()
			print('Purification Needed but memory not available --- exiting subtask')

		params = kwargs.get('params')
		if params != None:
			#Find memory_info for this memory object and 
			for memo in params:
				memory_info = self.task.task_manager.owner.resource_manager.memory_manager.get_info_by_memory(memo)

				#Find the subtask for this memory_info
				gen_subtask = self.task.task_manager.memory_to_gen_subtask[memory_info]
				gen_subtask.run()


	def is_eligible_to_run(self):
		#print('subtask:	self.dependencies in is_eligible_to_run', [d.name for d in self.dependencies])
		for dependency in self.dependencies:
			if dependency.status != 1:
				#print('False')
				return False
		#print('True')
		return True

#Each node has their separate Task Manager
class TaskManager:

	"""
		owner: node this task manager is attached to (quantum router)
	"""
	def __init__(self, owner: "QuantumRouter"):
		#Add task manager ids
		self.name = "task_manager"
		self.owner = owner
		"""         Structure
        	{task:{'dependencies': [], 'is_dependecy_of':[]}}"""
		self.task_map = {}
		self.memory_to_gen_subtask = {}
		
	def add_task(self,task: "Task", dependencies):
		"""
		#self.task_list.append(task)
		
		#task.creation_time = self.owner.timeline.now()
		entry = {}
		entry['dependencies'] = dependencies
		entry['is_dependecy_of'] = []
		
		#Map this newly created task in the is_dependency_list of dependencies
		for d in dependencies:
			self.task_map[d.id]['is_dependecy_of'].append(task)

		#Insert the entry in the task table
		self.task_map[task.id] = entry
		"""

		#Remove none vals
		dependencies = [i for i in dependencies if i != None]
		
		#print('depedencies for task:  ', task.name ,'  are  ', [i.name for i in dependencies if i != None])

		entry = {}
		entry['dependencies'] = dependencies
		entry['is_dependecy_of'] = []
		task.task_manager = self
		
		#Map this newly created task in the is_dependency_list of dependencies
		for d in dependencies:
			self.task_map[d]['is_dependecy_of'].append(task)

		#Insert the entry in the task table
		self.task_map[task] = entry

		#Initialize the dependency to subtask map for this task
		task.init_dependency_subtask_map()

	def run_task(self, task: "Task", **kwargs):
		#This handles the cases where memory is passed onto by the dependency task
		if 'memories_info' in kwargs:
			task.memories_info = kwargs['memories_info']
		
		if 'mem_indices' in kwargs:
			mem_indices = kwargs['mem_indices']
			tmp_mem_info = []
			for mem_index in mem_indices:
				tmp_mem_info.append(self.owner.resource_manager.memory_manager.__getitem__(mem_index))
			task.memories_info = tmp_mem_info
		
		dependency_subtasks = []
		if 'dependency_subtasks' in kwargs:
			dependency_subtasks = kwargs['dependency_subtasks']

		task.wakeup(self.owner.timeline.now())
		subtasks = task.action(task.memories_info, dependency_subtasks=dependency_subtasks)
		logging.debug('Running task:	' + str (task.name))
		
		for subtask in subtasks:
			subtask.task = task
			if subtask.is_eligible_to_run():
					subtask.run()

		task.has_already_run = True
	
	def subtask_success(self, subtask):
		# If subtask is a final_swap for a virtual link, we remember it
		#print(subtask.task.name, ' Task flag value: ', subtask.task.is_vl_final_swap_task)
		if subtask.task.is_vl_final_swap_task:
			responder = subtask.task.get_reservation().responder
			if responder == self.owner.name:
				responder = subtask.task.get_reservation().initiator
			
			#print('responder: ', responder)
			if responder not in self.owner.virtual_links:
				self.owner.virtual_links[responder] = [subtask]
			else:
				self.owner.virtual_links[responder].append(subtask)
			
			#print(f'Virtual links at : {self.owner.name} are : {self.owner.virtual_links}')
		
		#If subtask has dependents aready mapped, then execute them directly
		#print('In subtask_success')
		#print('subtask.dependents: ',len(subtask.dependents))
		if len(subtask.dependents) != 0:
			for dependent_subtask in subtask.dependents:
				if dependent_subtask.is_eligible_to_run():
					dependent_subtask.run()
			return

		#Get the parent task from this subtask and obtain its dependents
		dependent_tasks = self.task_map[subtask.task]['is_dependecy_of']
		#print('dependent_tasks for this: ', len(dependent_tasks))
		logging.debug('subtask success:	' + str(subtask.name))
		#Call the dependent task's dependency_subtask_map and append to it
		for dependent_task in dependent_tasks:
			dependent_task.set_dependency_to_subtask(subtask)

			#check if the dependent task can be executed now to instantiate a subtask
			flag, dependency_subtasks = dependent_task.is_eligible()
			if flag:
				#dependent_subtask = dependent_task.run()	#Create a subtask by running the dependent task along with passing the dependency subtask objects and memory indices
				memories_info = []
				for vals in dependency_subtasks:
					#print('dependency_subtasks name:	', vals.name)
					memories_info.extend(vals.memories_info)
				
				self.run_task(dependent_task, memories_info=memories_info, dependency_subtasks=dependency_subtasks)
				

	def subtask_failure(self, subtask):
		#Since subtask has failed we check if it was dependent on any other subtask and we keep on doing this till we reach the first subtask in the chain
		logging.debug('subtask failed:	' + str(subtask.name))
		logging.debug('initial dependencies for this subtask:	'+ str( [i.name for i in subtask.initial_dependency_subtasks]))
		for init_dep_subtask in subtask.initial_dependency_subtasks:
			# print(f'running init_dep_subtask: {init_dep_subtask.name}')
			init_dep_subtask.run()

	def initiate_tasks(self):
		#Loop over all the tasks and find the ones that don't have any dependencies associated
		#print("initiate_tasks running for node: ", self.owner.name)
		for task, task_details in self.task_map.items():
			#if len(task_details['dependencies']) == 0:
				#print('Trying to initiate task: ', task.name ,'and its already run flag is: ', task.has_already_run)

			#if task.can_run_on_init:
				#print('Trying to initiate task: ', task.name ,'and its can_run_on_init flag is: ', task.can_run_on_init)
			
			if len(task_details['dependencies']) == 0 and not task.has_already_run:
				self.run_task(task)
			
			if task.can_run_on_init:
				#check if the dependent task can be executed now to instantiate a subtask
				flag, dependency_subtasks = task.is_eligible()
				while flag:
					#dependent_subtask = dependent_task.run()	#Create a subtask by running the dependent task along with passing the dependency subtask objects and memory indices
					memories_info = []
					for vals in dependency_subtasks:
						#print('dependency_subtasks name:	', vals.name)
						memories_info.extend(vals.memories_info)
					
					self.run_task(task, memories_info=memories_info, dependency_subtasks=dependency_subtasks)
					flag, dependency_subtasks = task.is_eligible()


			
	def send_request(self, protocol, req_dst, req_condition_func):
		return self.owner.resource_manager.send_request(protocol, req_dst, req_condition_func)
