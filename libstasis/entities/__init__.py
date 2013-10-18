from libstasis.entities.operators import and_
from libstasis.interfaces import IAspects
from propdict import propdict
from sqlalchemy import create_engine, MetaData
from sqlalchemy import types
from sqlalchemy.schema import Column, ForeignKey, Table
from sqlalchemy.sql import select
from sqlalchemy.sql.operators import Operators


class Entities(object):
    def __init__(self, registry=None):
        self.registry = registry
        self.engine = create_engine('sqlite://')
        self.metadata = MetaData(self.engine)
        entity = Table(
            'entity', self.metadata,
            Column('id', types.Integer, primary_key=True))
        entity.create()
        self.aspects = propdict()

    def add_aspect(self, name, *columns):
        table = Table(
            name, self.metadata,
            Column('id', types.Integer, ForeignKey("entity.id")),
            *columns)
        table.create()
        self.aspects[name] = propdict(
            ((x.name, x) for x in columns),
            _name=name,
            _table=table)
        self._aspect_names = set(self.aspects.keys())

    def add_entity(self, aspects):
        if self.registry is not None:
            aspects = self.registry.getAdapter(aspects, IAspects)
        aspects = propdict(aspects)
        conn = self.engine.connect()
        tables = self.metadata.tables
        entity_id = conn.execute(tables['entity'].insert()).lastrowid
        for aspectname in self._aspect_names.intersection(aspects):
            table = tables[aspectname]
            data = aspects[aspectname]
            if isinstance(data, (propdict, dict)):
                conn.execute(table.insert().values(id=entity_id, **data))
            else:
                conn.execute(table.insert().values([entity_id, data]))

    def query(self, *args):
        conn = self.engine.connect()
        tables = self.metadata.tables
        entity = tables['entity']
        aspects = set()
        filters = []
        for arg in args:
            if isinstance(arg, Operators):
                filters.append(arg)
                children = list(arg.get_children())
                for child in children:
                    if isinstance(child, Column):
                        aspects.add(child.table)
                    elif isinstance(child, Operators):
                        children.extend(child.get_children())
            elif isinstance(arg, propdict):
                aspects.add(arg._table)
            else:
                aspects.add(tables[arg])
        fields = []
        joins = entity
        for aspect in aspects:
            fields.extend(aspect.columns.values()[1:])
            joins = joins.join(aspect)
        s = select(fields).select_from(joins)
        if filters:
            if len(filters) == 1:
                s = s.where(filters[0])
            else:
                s = s.where(and_(*filters))
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
