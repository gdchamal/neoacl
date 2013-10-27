from .helpers.base import BaseCore, Relation

from .models import (User as MUser, Resource as MResource,
                     Group as MGroup, HaveResource, HaveGroup,
                     Permission, InGroup)


class Resource(BaseCore):

    _model_class = MResource

    @property
    def user(self):
        obj = self.fetch("""start a=node(%d)
            match b-[:have_resource]->a return b""" % (self.eid))
        return User(obj)

    @classmethod
    def by_external_type_id(cls, type, external_id, doraise=True):
        query = """start a=node(*)
                match a-[:have_resource]-b
                where has(a.element_type) and
                a.element_type = "user" and
                b.type = "%s" and b.external_id = %d
                return b""" % (type, external_id)
        entities = cls.fetch_all(query)
        if entities and len(entities) == 1:
            return cls(entities[0])
        if doraise:
            raise ValueError("%s with external_id %s.%s not found" %
                             (cls.__name__, type, external_id))
        return None

    @classmethod
    def check_permission(self, user, type, ext_id, method):
        """Here magic happen, only a graph traversal query

        The question is: does this resource have method permission
        for user that must belong to a group having authorization
        """

        query = """start a=node(%d)
        match a<-[:in_group]-b-[p:permission]-c
        where c.type = "%s" and c.external_id = %d
        and p.method = "%s"
        return p""" % (user.eid, type, ext_id, method)
        perms = self.fetch_all(query)
        return True if perms else False


class Group(BaseCore):

    _model_class = MGroup

    relations = {
        'resources': Relation(Resource, Permission, min=0),
        'users': Relation('User', InGroup, min=0),
    }


class User(BaseCore):

    _model_class = MUser

    relations = {
        'groups': Relation(Group, HaveGroup, min=0),
        'resources': Relation(Resource, HaveResource, min=0),
    }

    @classmethod
    def by_external_id(cls, external_id, doraise=True):
        obj = cls.get_proxy().index.lookup(external_id=external_id)
        if obj:
            return cls(obj.next())
        if doraise:
            raise ValueError("%s with external_id %s not found" %
                             (cls.__name__, external_id))
        return None

    def list_permissions(self, filters=None):
        query = """start a=node(%d)
        match a-[:in_group]-(b)-[p:permission]-(c)
        return b.name as group, p.method as method,
        c.type as resource_type, c.external_id as resource_id""" % (self.eid)
        results = self.fetch_table(query)
        return results
