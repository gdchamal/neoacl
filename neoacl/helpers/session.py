from bulbs.neo4jserver import Graph
from bulbs.config import Config as GraphConfig
from .conf import CONF

_graph = None


def get_graph():
    global _graph
    if not _graph:
        graph_config = GraphConfig(CONF['database']['url'])
        graph_config.set_logger(CONF['database']['log_level'])
        _graph = Graph(graph_config)
    return _graph
