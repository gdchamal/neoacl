from .helpers.session import get_graph
from core import User, Resource, Group, Permission


class UserError(Exception):
    pass


class GroupError(Exception):
    pass


class PermissionError(Exception):
    pass


class BaseManager(object):

    def __init__(self):
        self.graph = get_graph()


class BaseUserManager(BaseManager):

    def __init__(self, username):
        BaseManager.__init__(self)
        self.user = self._check_user(username)

    def _check_user(self, username):
        user = User.by_name(username, False)
        if not user:
            raise UserError('Invalid user %s' % username)
        return user


class AdminManager(BaseManager):

    def create_user(self, username, ext_id):
        exist = User.by_name(username, False)
        if exist:
            raise UserError('User %s already exist' % username)
        user = User.create(name=username, external_id=ext_id)
        return user.eid

    def delete_user(self, username, ext_id=0):
        user = User.by_name(username, False)
        if not user:
            raise UserError('User %s not found' % username)
        if ext_id:
            if user.external_id != ext_id:
                raise UserError('Invalid external id for user %s' % username)
        user.delete()

    def get_user(self, username):
        user = User.by_name(username, False)
        if not user:
            raise UserError('User %s not found' % username)
        return user


class UserManager(BaseUserManager):

    def _list_entities(self, entity, filters=None):
        # XXX : implement filters
        return getattr(self.user, entity)

    def list_resources(self, filters=None):
        return self._list_entities('resources', filters)

    def list_groups(self, filters=None):
        return self._list_entities('groups', filters)

    def list_permissions(self, filters=None):
        return self.user.list_permissions(filters)

    def create_resource(self, type, ext_id):
        name = '%s#%d' % (type, ext_id)
        # XXX : check if exist on type, ext_id
        resource = Resource.create(name=name, type=type, external_id=ext_id)
        self.user._attach('resources', resource)
        return resource.eid

    def delete_resource(self, type, ext_id):
        raise NotImplementedError()

    def create_group(self, name, description=None):
        exist = Group.by_name(name, False)
        if exist:
            raise GroupError('Group %s already exist for user %s' %
                             (name, exist.user.name))
        group = Group.create(name=name, description=description)
        self.user._attach('groups', group)
        return group.eid

    def delete_group(self, name):
        raise NotImplementedError()

    def group_add_user(self, groupname, username):
        user = self._check_user(username)
        group = Group.by_name(groupname, False)
        if not group:
            raise GroupError('Group %s not found' % groupname)
        # XXX : do better list comprehension with core object
        if not group.eid in [x.eid for x in self.user.groups]:
            raise PermissionError('Permission denied for user %s' %
                                  (self.user.name))
        if user.eid in [x.eid for x in group.users]:
            raise GroupError('User %s already in group %s' %
                             (username, groupname))
        rel = group._attach('users', user)
        return rel.eid

    def group_delete_user(self, groupname, username):
        raise NotImplementedError()

    def allow(self, type, resource_ext_id, group_name, **kwargs):
        # XXX : not kwargs, method instead
        group = Group.by_name(group_name)
        resource = Resource.by_external_type_id(type, resource_ext_id)
        # XXX factorize
        if not group.eid in [x.eid for x in self.user.groups]:
            raise PermissionError('Permission denied for %s' %
                                  (self.user.name))
        if not resource.eid in [x.eid for x in self.user.resources]:
            raise PermissionError('Permission denied for %s' %
                                  (self.user.name))
        relation = group._attach('permissions', resource, **kwargs)
        return relation.eid

    def revoke(self, rule_id):
        # XXX check relation belong to user
        # XXX index by internal vertice is not ok
        rule = Permission.by_id(rule_id)
        if not rule:
            raise PermissionError('No such permission %d' % rule_id)
        rule.delete()
        return True


class PermissionManager(BaseUserManager):

    def check(self, username, type, ext_id, method='read'):
        """"Rule them all"""
        resource = Resource.by_external_type_id(type, ext_id)
        user = self._check_user(username)
        if not resource:
            raise PermissionError('Invalid resource')
        perms = resource.check_permission(self.user, user, method)
        return True if perms else False
