from enum import IntEnum


class DurabilityQosPolicyKind(IntEnum):
    VOLATILE_DURABILITY_QOS = 0,
    TRANSIENT_LOCAL_DURABILITY_QOS = 1,
    TRANSIENT_DURABILITY_QOS = 2,
    PERSISTENT_DURABILITY_QOS = 3


class ReliabilityQosPolicyKind(IntEnum):
    BEST_EFFORT_RELIABILITY_QOS = 0,
    RELIABLE_RELIABILITY_QOS = 1


class HistoryQosPolicyKind(IntEnum):
    KEEP_LAST_HISTORY_QOS = 0,
    KEEP_ALL_HISTORY_QOS = 1


class DurabilityQosPolicy:
    def __init__(self):
        self.kind = DurabilityQosPolicyKind.VOLATILE_DURABILITY_QOS


class ReliabilityQosPolicy:
    def __init__(self):
        self.kind = ReliabilityQosPolicyKind.BEST_EFFORT_RELIABILITY_QOS
        self.max_blocking_time = 0


class HistoryQosPolicy:
    def __init__(self):
        self.kind = HistoryQosPolicyKind.KEEP_LAST_HISTORY_QOS
        self.depth = 1


class DataWriterQos:
    def __init__(self):
        self.durability = DurabilityQosPolicy()
        self.reliability = ReliabilityQosPolicy()
        self.history = HistoryQosPolicy()


class DataReaderQos:
    def __init__(self):
        self.durability = DurabilityQosPolicy()
        self.reliability = ReliabilityQosPolicy()
        self.history = HistoryQosPolicy()
