
neoacl is a python package for simple ACL management using a neo4j backend.
It's oriented to delegate permission for a group of user to another user
resource.

No authentication, nor authorization is supported, it's outside scope of
this component.

Your application must create their user in this component. This done the
user gain full privileges on their groups and resources and rule between
them.

Simples methods are then needed to test in your application if an user
had a delegated permission to access a resource of another user.

There is 3 different context manager to implement in your application.

1 - AdminManager

used to create, delete users

from neoacl.manager import AdminManager
m = AdminManager()

m.create_user('test1')
m.create_user('test2')

2 - User Manager

used to define resources and groups that belong to an user.

Others users must be included in groups, and permissions
between group and resource allowed to permit minimal working
data.

from neoacl.manager import UserManager
m = UserManager('test1')
m.create_resource('server', 123)
m.create_group('admin_server')
m.group_add_user('admin_server', 'test2')

# Permit read access on server 123 to group admin_server
m.allow('server', 123, 'admin_server', 'read')


3 - Permission Manager

That the aim of this component, to simpliy permit permission
check against resource for a user.

from neoacl.manager import PermissionManager
m = PermissionManager('test2')

if m.check('server', 123, 'read'):
    return "Access granted"
else:
    return "Access denied"
