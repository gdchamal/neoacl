from bulbs.model import Node, Relationship
from bulbs.property import String, Integer, DateTime, Bool
from bulbs.utils import current_datetime


class BaseModel(Node):
    date_insert = DateTime(default=current_datetime)
    date_update = DateTime(nullable=True)


class BaseRelation(Relationship):
    date_insert = DateTime(default=current_datetime)


class User(BaseModel):

    element_type = "user"
    name = String(nullable=False)
    external_id = Integer(nullable=False)


class Resource(BaseModel):

    element_type = 'resource'
    name = String(nullable=False)
    external_id = Integer(nullable=False)
    # XXX : use an enumerated list of values
    type = String(nullable=False)


class Group(BaseModel):

    element_type = 'group'
    name = String(nullable=False)
    description = String()


class HaveResource(BaseRelation):

    label = 'have_resource'


class HaveGroup(BaseRelation):

    label = 'have_group'


class Permission(BaseRelation):

    label = 'permission'
    method = String(nullable=False)
