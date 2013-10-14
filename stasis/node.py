from pyramid.location import lineage
from stasis.interfaces import INodeFactory
import os


class Node(object):
    def __init__(self, registry, path=None, root=None):
        self.path = path if path is not None else ''
        self.root = root
        self.__parent__ = None
        self.__name__ = ''
        self.registry = registry
        self.items = {}

    @property
    def abspath(self):
        root = list(lineage(self))[-1].root
        return os.path.join(
            self.registry['path'],
            root,
            self.path)

    def __getitem__(self, name):
        if name not in self.items:
            path = os.path.join(self.path, name)
            ext = os.path.splitext(path)[1]
            factory = self.registry.queryUtility(
                INodeFactory, name=ext, default=Node)
            self.items[name] = factory(self.registry, path)
            self.items[name].__parent__ = self
            self.items[name].__name__ = name
        return self.items[name]

    def __iter__(self):
        return iter(self.items)

    def __call__(self, request):
        return self
