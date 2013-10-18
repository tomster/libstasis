from pytest import fixture
from propdict import propdict
from libstasis.entities import Entities
from libstasis.entities import Column, types


@fixture
def entities():
    entities = Entities()
    entities.add_aspect('size', Column('value', types.Integer))
    entities.add_aspect('name', Column('value', types.Unicode))
    return entities


def test_add_entities(registry, entities):
    entities.add_entity(propdict(size=23, name=u'foo'))
    entities.add_entity(propdict(size=42, name=u'bar'))
    result = entities.query('size', 'name')
    assert len(result) == 2
    assert result[0].size.value == 23
    assert result[0].name.value == u'foo'
