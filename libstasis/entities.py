from libstasis.interfaces import IAspects
from propdict import propdict
from sqlalchemy import create_engine, MetaData
from sqlalchemy import types
from sqlalchemy.schema import Column, ForeignKey, Table
from sqlalchemy.sql import select


class Entities(object):
    def __init__(self, registry=None):
        self.registry = registry
        self.engine = create_engine('sqlite://')
        self.metadata = MetaData(self.engine)
        entity = Table(
            'entity', self.metadata,
            Column('id', types.Integer, primary_key=True))
        entity.create()
        self.aspects = dict()

    def add_aspect(self, name, *columns):
        table = Table(
            name, self.metadata,
            Column('id', types.Integer, ForeignKey("entity.id")),
            *columns)
        table.create()
        self.aspects[name] = [x.name for x in columns]
        self.aspect_names = set(self.aspects.iterkeys())

    def add_entity(self, aspects):
        if self.registry is not None:
            aspects = self.registry.getAdapter(aspects, IAspects)
        aspects = propdict(aspects)
        conn = self.engine.connect()
        tables = self.metadata.tables
        entity_id = conn.execute(tables['entity'].insert()).lastrowid
        for aspect in self.aspect_names.intersection(aspects):
            table = tables[aspect]
            data = aspects[aspect]
            if isinstance(data, (propdict, dict)):
                conn.execute(table.insert().values(id=entity_id, **data))
            else:
                conn.execute(table.insert().values([entity_id, data]))

    def query(self, *aspects, **kw):
        conn = self.engine.connect()
        tables = self.metadata.tables
        entity = tables['entity']
        aspect_names = set(aspects).union(kw.iterkeys())
        aspects = [tables[x] for x in aspect_names]
        fields = []
        joins = entity
        for aspect in aspects:
            fields.extend(aspect.columns.values()[1:])
            joins = joins.join(aspect)
        s = select(fields).select_from(joins)
        result = conn.execute(s)
        rows = []
        for row in result:
            data = propdict()
            for column, value in zip(fields, row):
                data.setdefault(column.table.name, propdict())[column.name] = value
            rows.append(data)
        return rows


def add_entity_aspect(config, name, *columns):
    def register():
        config.registry['entities'].add_aspect(name, *columns)
    config.action(('entity-aspect', name), register)


def includeme(config):
    config.registry['entities'] = Entities(config.registry)
    config.add_directive('add_entity_aspect', add_entity_aspect)
