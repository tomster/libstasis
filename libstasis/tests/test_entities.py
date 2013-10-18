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


def test_query_filter(registry, entities):
    entities.add_entity(propdict(size=23, name=u'foo'))
    entities.add_entity(propdict(size=42, name=u'bar'))
    a = entities.aspects
    result = entities.query(a.size.value > 23, a.name)
    assert len(result) == 1
    assert result[0].size.value == 42
    assert result[0].name.value == u'bar'


def test_multiple_query_filter(registry, entities):
    entities.add_entity(propdict(size=23, name=u'foo'))
    entities.add_entity(propdict(size=23, name=u'bar'))
    entities.add_entity(propdict(size=42, name=u'bar'))
    a = entities.aspects
    result = entities.query(a.size.value == 23, a.name.value == u'bar')
    assert len(result) == 1
    assert result[0].size.value == 23
    assert result[0].name.value == u'bar'


def test_complex_query_filter(registry, entities):
    from sqlalchemy.sql.operators import or_
    entities.add_entity(propdict(size=23, name=u'foo'))
    entities.add_entity(propdict(size=42, name=u'bar'))
    a = entities.aspects
    result = entities.query(or_(a.size.value == 1, a.size.value == 42), a.name)
    assert len(result) == 1
    assert result[0].size.value == 42
    assert result[0].name.value == u'bar'
