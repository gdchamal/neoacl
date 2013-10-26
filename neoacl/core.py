from .helpers.base import (BaseCore, Relation, CoreException, CoreExists)
from .helpers.conf import CONF

from .models import (User as MUser, Resource as MResource,
                     Group as MGroup, haveResource, haveGroup, allow)


class User(BaseCore):

    _model_class = MUser


class Resource(BaseCore):

    _model_class = MResource


class Group(BaseCore):

    _model_class = MGroup
