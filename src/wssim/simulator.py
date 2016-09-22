"""
provides Simulator class containing the global simulation state.
"""
from heapq import heappush, heappop
from collections import defaultdict
from wssim.processor import Processor
from wssim.logger import Logger
from wssim.events import IdleEvent

class Simulator:
    """
    Simulation
    """
    def __init__(self, processors_number, log_file, topology):
        self.log_file = log_file
        self.time = 0
        self.total_work = 0
        self.logger = None
        self.topology = topology
        self.remote_steal_probability = None
        if __debug__:
            if self.log_file is not None:
                self.logger = Logger(log_file, self)
        self.events = list()
        self.processors = list()
        # associate to each processor the next valid event
        # we do that since the heap contains cancelled events which we
        # cannot remove
        self.valid_events = dict()
        self.init_processors(processors_number)
        self.steal_info = defaultdict(int)
        if __debug__:
            if self.log_file is not None:
                self.platform_definition_logger(2)

    def reset(self, work):
        """
        sets work, create all initial events
        """
        self.valid_events.clear()
        self.events.clear()
        self.total_work = work
        self.time = 0
        self.steal_info.clear()
        # self.init_stealing_probabilities(remote_steal_probability)
        for index, processor in enumerate(self.processors):
            processor.current_time = 0
            processor.network_time = 0
            if index:
                self.add_event(IdleEvent(0, processor))
                processor.work = 0
            else:
                self.add_event(IdleEvent(work//processor.speed, processor))
                processor.work = work

    def run(self):
        """
        start Simulation of the system
        """
        while self.total_work > 0:
            event = self.next_event()
            self.time = event.time
            event.execute()
        if __debug__:
            if self.log_file is not None:
                self.logger.end_of_logger(clusters_number=2,
                                          processors_number=len(
                                              self.processors))

    def add_event(self, event):
        """
        add given event to system.
        pre-requisite : event's time is >= simulator's time
        """
        heappush(self.events, event)
        # newest event is always the valid one
        assert isinstance(event.processor, Processor)
        self.valid_events[event.processor] = event

    def next_event(self):
        """
        returns the next valid event to take place.
        """
        # loop discarding all cancelled events
        event = heappop(self.events)
        while event != self.valid_events[event.processor]:
            event = heappop(self.events)
        return event

    def init_processors(self, processors_number):
        """
        cree l'ensemble des processor
        """
        cluster = self.topology.cluster_number(0)
        self.processors.append(Processor(0, cluster, self, self.total_work))
        for id_processor in range(1, processors_number):
            cluster = self.topology.cluster_number(id_processor)
            self.processors.append(Processor(id_processor, cluster, self))

    def communication_end_time(self, source, destination):
        """
        return time when communication between source and destination
        processors will end if we start it now.
        """
        return self.time +\
            self.topology.distance(source.number, destination.number)

    def platform_definition_logger(self, clusters_number):
        """
        log to create platform definition,
            clusters and processors with their names and numbers
        """
        # Create Clusters.
        for id_cluster in range(clusters_number):
            self.logger.add_cluster(id_cluster)

        # Create Processors.
        for processor in self.processors:
            self.logger.add_processor(processor)

        # set (update) intial state Processors.
        for processor in self.processors:
            if processor.number == 0:
                self.logger.update_processor_state(processor,
                                                   new_state="Executing")
            else:
                self.logger.update_processor_state(processor,
                                                   new_state="Idle")
        # set initial work Processors.
        for processor in self.processors:
            if processor.number == 0:
                self.logger.set_work(processor, self.total_work)
            else:
                self.logger.set_work(processor)

    def init_stealing_probabilities(self, remote_steal_probability):
        """
        compute for each processor the probability vector used
        for stealing.
        pre-condition: processors are ordered by number
        """
        processors_number = len(self.processors)
        cluster_sizes = [processors_number // 2,
                         processors_number - processors_number//2]
        for processor in self.processors:
            probabilities = []
            for other_processor in self.processors:
                if other_processor == processor:
                    continue
                elif other_processor.cluster == processor.cluster:
                    probability = (1 - remote_steal_probability)\
                        /(cluster_sizes[processor.cluster] -1)
                else:
                    probability = remote_steal_probability\
                        /cluster_sizes[other_processor.cluster]
                probabilities.append((probability, other_processor))
            processor.compute_stealing_probabilities(probabilities)