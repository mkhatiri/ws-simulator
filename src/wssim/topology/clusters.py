"""
topology related functions for 2 clusters.
"""
from random import uniform, randint


class Topology:
    """
    Store all topology related informations and methods.
    """
    def __init__(self, processors_number, is_tasks,
                 local_latency=1, remote_latency=None,
                 remote_steal_probability=None):
        self.processors_number = processors_number
        self.latencies = [remote_latency, local_latency]
        self.remote_steal_probability = remote_steal_probability
        self.cluster_sizes = [self.processors_number//2]
        self.cluster_sizes.append(self.processors_number -
                                  self.cluster_sizes[0])
        self.cluster_starts = [0, self.cluster_sizes[0]]
        self.remote_granularity = None
        self.local_granularity = None
        self.is_tasks = is_tasks

    def distance(self, *processor_numbers):
        """
        Returns distance between the two given processors numbers.
        """
        assert self.latencies[0] is not None
        clusters = [self.cluster_number(p) for p in processor_numbers]
        return self.latencies[clusters[0] == clusters[1]]

    def update_remote_latency(self, remote_latency):
        """
        Set remote latency.
        """
        self.latencies[0] = remote_latency

    def cluster_number(self, processor_id):
        """
        return cluster id for given processor
        """
        if processor_id < self.processors_number // 2:
            return 0
        else:
            return 1

    def update_granularity(self, local_granularity, remote_granularity, 
                           threshold):
        """
        update local and remote grenularity,
        """
        if local_granularity is None:
            self.local_granularity = threshold
        else:
            self.local_granularity = local_granularity
            assert local_latency >= threshold

        if remote_granularity is None:
            self.remote_granularity = threshold
        else:
            self.remote_granularity = remote_granularity
            assert remote_granularity >= threshold

    def select_victim_not(self, unwanted_processor_number):
        """
        select a random target not unwanted_processor_number.
        """
        cluster = self.cluster_number(unwanted_processor_number)
        if uniform(0, 1) < self.remote_steal_probability:
            target_cluster = 1 - cluster
        else:
            target_cluster = cluster

        target_number = unwanted_processor_number
        while target_number == unwanted_processor_number:
            target_number = self.cluster_starts[target_cluster] +\
                randint(0, self.cluster_sizes[target_cluster]-1)
        return target_number
