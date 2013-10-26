from .helpers.session import get_graph
from core import User, Resource, Group


class UserError(Exception):
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


class UserManager(BaseUserManager):

    def __init__(self, username):
        BaseManager.__init__(self)
        self.user = self._check_user(username)

    def _list_entities(self, entity, filters=None):
        # XXX : implement filters
        return getattr(self.user, entity)

    def list_resources(self, filters=None):
        return self._list_entities('resources', filters)

    def list_groups(self, filters=None):
        return self._list_entities('groups', filters)

    def list_permissions(self, filters=None):
        return self.user.list_permissions(filters)

    def create_resource(self, name, type, ext_id):
        # XXX : check if exist on type, ext_id
        resource = Resource.create(name=name, type=type, external_id=ext_id)
        self.user._attach('resources', resource)
        return resource.eid

    def create_group(self, name, description=None):
        exist = Group.by_name(name, False)
        if exist:
            raise GroupError('Group %s already exist for user %s' %
                             (name, exist.user.name))
        group = Group.create(name=name, description=description)
        self.user._attach('groups', group)
        return group.eid

    def allow(self, resource_id, group_id, **kwargs):
        # XXX Check resource and group belong to user
        group = Group.by_id(group_id)
        resource = Resource.by_id(resource_id)
        # XXX check group belong to user
        relation = group._attach('permissions', resource, **kwargs)
        return relation.eid

    def revoke(self, rule_id):
        # XXX check relation belong to user
        rule = Permission.by_id(rule_id)
        if not rule:
            raise PermissionError('No such permission %d' % rule_id)
        rule.delete()
        return True


class PermissionManager(BaseUserManager):

    def check(self, to_username, type, ext_id, method='read'):
        """"Rule them all"""
        resource = Resource.by_external_type_id(type, ext_id)
        if not resource:
            raise PermissionError('Invalid resource')
        if resource.user.eid != self.user.eid:
            raise PermissionError('Permission denied')
        perms = resource.check_permission(to_username, method)
        return True if perms else False
