from .helpers.base import (BaseCore, Relation, CoreException, CoreExists)
from .helpers.conf import CONF

from .models import (User as MUser, Resource as MResource,
                     Group as MGroup, HaveResource, HaveGroup, Permission)


class Resource(BaseCore):

    _model_class = MResource

    @property
    def user(self):
        obj = self.fetch("""start a=node(%d)
            match b-[:have_resource]->a return b""" % (self.eid))
        return User(obj)

    @classmethod
    def by_external_type_id(cls, type, external_id):
        query = """start a=node(*)
                match a-[:have_resource]-b
                where has(a.element_type) and
                a.element_type = "user" and
                b.type = "%s" and b.external_id = %d
                return b""" % (type, external_id)
        entities = cls.fetch_all(query)
        if entities and len(entities) == 1:
            return cls(entities[0])
        raise ValueError("%s with external_id %s.%s not found" %
                         (cls.__name__, type, external_id))

    def check_permission(self, username, method):
        """Here magic happen, only a graph traversal query

        The question is: does this resource have method permission
        for user that must belong to a group having authorization
        """

        query = """start a=node(%d)
        match a-[p:have_permission]-(b)-[:have_group]-(c)
        where c.name = "%s"
        and p.method = "%s"
        return b""" % (self.eid, username, method)
        groups = self.fetch_all(query)
        return [Group(x) for x in groups]


class Group(BaseCore):

    _model_class = MGroup

    relations = {
        'permissions': Relation(Resource, Permission, min=0),
    }


class User(BaseCore):

    _model_class = MUser

    relations = {
        'groups': Relation(Group, HaveGroup, min=0),
        'resources': Relation(Resource, HaveResource, min=0),
    }

    @classmethod
    def by_external_id(cls, external_id):
        obj = cls.get_proxy().index.lookup(external_id=external_id)
        if obj:
            return cls(obj.next())
        if doraise:
            raise ValueError("%s with external_id %s not found" %
                             (cls.__name__, mbid))
        return None

    def list_permissions(self, filters=None):
        query = """start a=node(%d)
        match a-[:have_group]-(b)-[p:have_permission]-(c)
        return p.method, c"""
        results = self.fetch_all(query)
        return results
