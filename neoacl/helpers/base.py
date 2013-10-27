from copy import copy
from .session import get_graph

# A global registry is used for core objects discovered when imported
core_registry = {}


class CoreException(Exception):
    pass


class CoreExists(CoreException):
    pass


def get_core(node):
    """
    Lookup core registry and return class related to node
    """
    if not node.element_type in core_registry.keys():
        raise CoreException('Unknow core object type %s' % node.element_type)
    return core_registry[node.element_type](node)


class Relation(object):
    def __init__(self, dest, edge, min=0, max=None, can_attach=False):
        self._dest = dest
        self.edge = edge
        self.min = min
        self.max = max
        self.can_attach = can_attach

    @property
    def dest(self):
        """Defer lookup of class, avoid circular dependency evil"""

        # XXX: find another way to find module
        if isinstance(self._dest, str):
            module = __import__('neoacl.core', fromlist=self._dest)
            return getattr(module, self._dest)
        return self._dest


class BaseGraph(object):
    """Base Cypher query methods"""

    @classmethod
    def fetch(cls, query):
        q = get_graph().cypher.query(query)
        if q:
            return q.next()
        return None

    @classmethod
    def fetch_all(cls, query):
        q = get_graph().cypher.query(query)
        if not q:
            return []

        return list(q)

    @classmethod
    def fetch_table(cls, query):
        q = get_graph().cypher.table(query)
        if not q:
            return []

        return list(q)


class BaseCore(BaseGraph):
    """Abstract base class for graph core object"""
    class __metaclass__(type):
        def __init__(cls, name, bases, dict):
            type.__init__(cls, name, bases, dict)
            if cls._model_class:
                element_type = cls._model_class.element_type
                if not core_registry.get(element_type):
                    core_registry.update({element_type: cls})

    _model_class = None

    # Association a relation name to the core class to instanciante
    relations = {}

    def __init__(self, model_obj):
        self._model = model_obj

    @property
    def graph(self):
        return get_graph()

    @classmethod
    def get_proxy(cls):
        graph = get_graph()
        if not hasattr(graph, cls._model_class.element_type):
            graph.add_proxy(cls._model_class.element_type, cls._model_class)
        f = getattr(graph, cls._model_class.element_type)
        return f

    @classmethod
    def get_proxy_relation(cls, edge):
        graph = get_graph()
        if not hasattr(graph, edge.label):
            # XXX : whoo relation inception
            graph.add_proxy(edge.label, edge)
        f = getattr(graph, edge.label)
        return f

    @classmethod
    def by_id(cls, id):
        obj = cls.get_proxy().get(id)
        return cls(obj)

    @classmethod
    def by_name(cls, name, doraise=True):
        obj = cls.get_proxy().index.lookup(name=name)
        if obj:
            return cls(obj.next())
        if doraise:
            raise ValueError(name)
        return None

    @classmethod
    def all(cls):
        objs = cls.get_proxy().get_all()
        if objs:
            return [cls(o) for o in list(objs)]
        return []

    @classmethod
    def create(cls, **kwargs):
        # remove relations from args, make a real relation after
        # object created
        to_links = []
        for rel_name, relation in cls.relations.iteritems():
            if relation.min > 0 and not rel_name in kwargs:
                raise CoreException(
                    'Mandatory relation %s not found' % rel_name)
            if rel_name in kwargs:
                rel_id = kwargs.pop(rel_name)
                if hasattr(rel_id, 'eid'):
                    rel_id = rel_id.eid
                rel_obj = relation.dest.by_id(rel_id)
                if not isinstance(rel_obj, relation.dest):
                    raise CoreException(
                        "Invalid object id for relation %s" % (rel_name))
                if not rel_obj:
                    raise CoreException(
                        'Invalid id %d for relation %s' % (rel_id, rel_name))
                to_links.append((rel_name, rel_obj, relation.edge))

        obj = cls.get_proxy().create(kwargs)
        # Create relations
        for rel, rel_obj, edge in to_links:
            proxy = cls.get_proxy_relation(edge)
            proxy.create(obj, rel_obj._model)
        return cls(obj)

    def update(self, **kwargs):
        # XXX filter only attributes valid for model
        data = self._model.data()
        data.update(**kwargs)
        obj = self.get_proxy().update(self._model.eid, data)
        return True

    def delete(self):
        res = self.get_proxy().delete(self._model.eid)
        return True

    def __getattr__(self, key):
        # Be evil ...
        if key in self.relations.keys():
            related = self.get_related(key)
            if not related:
                return []
            return related
        return getattr(self._model, key)

    def get_related(self, relation):
        relation = self.relations[relation]
        models = self.fetch_all(
            'start a=node(%d) match a-[:%s]->(b) return b' %
            (self._model.eid, relation.edge.label))
        if relation.min == 1 and relation.max == 1 and len(models):
            return relation.dest(models[0])
        return [relation.dest(x) for x in models]

    def is_related(self, relation, obj):
        relation = self.relations[relation]
        edges = self._model.outE(relation.edge.label)
        if not edges:
            return False
        if obj.eid in [x.inV().eid for x in list(edges)]:
            return True
        return False

    def _attach(self, relation, obj, **kwargs):
        if self.is_related(relation, obj):
            raise CoreException('%s already attached to %s'
                                (relation, self.name))
        edge = self.relations[relation].edge
        proxy = self.get_proxy_relation(edge)
        # Validate constraint on relation
        # self._check_relation(relation, obj)
        edge = proxy.create(self._model, obj._model, **kwargs)
        return edge

    def _detach(self, relation, obj):
        if not self.is_related(relation, obj):
            raise CoreException('%s not attached to %s' %
                                (relation, self.name))
        g = get_graph()
        edge = self.relations[relation].edge
        edges = self._model.outE(edge.label)
        if not edges:
            return 0
        cpt = 0
        for e in list(edges):
            if e.inV().eid == obj.eid:
                g.edges.delete(e.eid)
                cpt += 1
        return cpt

    def data(self):
        d = copy(self._model.data())
        d.update(id=self._model.eid)
        return d

    def serialize(self, relations=False, expand=[]):
        d = self.data()
        if relations:
            for r in self.relations.keys():
                related = []
                if r in expand:
                    for x in self.get_related(r):
                        related.append(x.serialize(relations=True))
                else:
                    relate = self.get_related(r)
                    if isinstance(relate, list):
                        related = [x.data() for x in relate]
                    else:
                        related = relate.data()
                d.update({r: related})
        return d
