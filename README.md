
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