from dirtools import Dir
from libstasis.entities import Column, types
from zope.interface import Interface
import os


class IWalkerFileType(Interface):
    pass


class File(object):
    def __init__(self, walker, filepath):
        self.walker = walker
        self.filepath = filepath


class Walker(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path

    def walk(self, site):
        add_entity = site.registry['entities'].add_entity
        q = site.registry.queryUtility
        path = os.path.join(site.registry['path'], self.path)
        filenames = Dir(path).files()
        for filename in filenames:
            filepath = os.path.join(path, filename)
            ext = os.path.splitext(filepath)[1]
            factory = q(IWalkerFileType, name=ext, default=File)
            add_entity(factory(self.name, filepath))


def add_filesystem_walker(config, name, path):
    def subscriber(event):
        Walker(name, path).walk(event.site)
    config.add_subscriber(subscriber, "stasis.events.PreBuild")


def add_walker_file_type(self, name, reader):
    reader = self.maybe_dotted(reader)

    def register():
        self.registry.registerUtility(reader, IWalkerFileType, name=name)

    self.action((IWalkerFileType, name), register)


def includeme(config):
    config.registry['entities'].add_aspect(
        'walker',
        Column('name', types.Unicode))
    config.add_directive('add_filesystem_walker', add_filesystem_walker)
    config.add_directive('add_walker_file_type', add_walker_file_type)
