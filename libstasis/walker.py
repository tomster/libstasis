from dirtools import Dir
from libstasis.entities import Column, types
from zope.interface import Interface
import os


class IWalkerFileType(Interface):
    pass


class File(object):

    @property
    def filepath(self):
        return os.path.join(self.basepath, self.subpath)

    def __init__(self, walker, basepath, subpath):
        self.walker = walker
        self.basepath = basepath
        self.subpath = subpath


class Walker(object):
    def __init__(self, name=None, path=''):
        self.name = name
        self.path = path

    def walk(self, site):
        add_entity = site['entities'].add_entity
        q = site.queryUtility
        basepath = os.path.join(site['path'], self.path)
        subpaths = Dir(basepath).files()
        for subpath in subpaths:
            filepath = os.path.join(basepath, subpath)
            ext = os.path.splitext(filepath)[1]
            factory = q(IWalkerFileType, name=ext, default=File)
            add_entity(factory(self.name, basepath=basepath, subpath=subpath))


def add_filesystem_walker(config, name, path):
    def subscriber(event):
        Walker(name=name, path=path).walk(event.site)
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
