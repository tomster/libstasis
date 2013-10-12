from ConfigParser import RawConfigParser
from contextlib import contextmanager
from imp import new_module
from pprint import pformat
from pyramid.asset import resolve_asset_spec
from pyramid.config import Configurator as BaseConfigurator
from pyramid.config.predicates import TraversePredicate
from pyramid.interfaces import IRequestExtensions, ITweens
from pyramid.path import caller_package
from pyramid.router import Router
from pyramid.scripting import _make_request
from pyramid.traversal import traverse
from pyramid.urldispatch import _compile_route
from pyramid.util import action_method
from stasis.interfaces import INodeFactory
import logging
import os
import sys


log = logging.getLogger('Stasis')


class Node(object):
    def __init__(self, registry, path):
        self.path = path
        self.registry = registry
        self.items = {}

    def __getitem__(self, name):
        if name not in self.items:
            path = os.path.join(self.path, name)
            ext = os.path.splitext(path)[1]
            factory = self.registry.queryUtility(
                INodeFactory, name=ext, default=Node)
            self.items[name] = factory(self.registry, path)
        return self.items[name]

    def __iter__(self):
        return iter(self.items)

    def __call__(self, request):
        return self

    def load(self):
        if os.path.isdir(self.path):
            raise ValueError("Trying to load a directory node at '%s'." % self.path)
        log.debug("No handler for loading '%s'." % self.path)


class Configurator(BaseConfigurator):
    @action_method
    def add_node_factory(self, name, factory):
        factory = self.maybe_dotted(factory)
        if not name:
            name = ''

        def register():
            self.registry.registerUtility(factory, INodeFactory, name=name)

        intr = self.introspectable('node factories',
                                   name,
                                   self.object_description(factory),
                                   'node factory')
        intr['factory'] = factory
        intr['name'] = name
        self.action((INodeFactory, name), register,
                    introspectables=(intr,))

    @action_method
    def add_static_view(self, name, path, **kw):
        spec = self._make_spec(path)
        kw['traverse'] = '/%s/*subpath' % resolve_asset_spec(spec)[1]
        BaseConfigurator.add_static_view(self, name, path, **kw)


def read_config(path):
    config = RawConfigParser()
    config.optionxform = lambda s: s
    config.read(path)
    return dict(
        (x, dict(
            (y, config.get(x, y))
            for y in config.options(x)))
        for x in config.sections())


def static_path(request, path, **kw):
    if not os.path.isabs(path):
        if not ':' in path:
            package = caller_package()
            path = '%s:%s' % (package.__name__, path)
    kw['_app_url'] = ''
    path = request.static_url(path, **kw)
    return os.path.relpath(path, os.path.dirname(request.path))


@contextmanager
def main_module(module):
    sys.modules['__main__'] = module
    sys.modules['here'] = module
    yield
    for name in sys.modules.keys():
        if name.startswith('__main__'):
            del sys.modules[name]
    del sys.modules['here']


class Site(object):
    def __init__(self, path):
        config_py = os.path.join(path, 'config.py')
        if not os.path.lexists(config_py):
            raise ValueError("No config.py found at '%s'." % path)
        self.path = path
        self.path_len = len(path)
        self.config = read_config(os.path.join(path, 'site.cfg'))
        self.outpath = os.path.join(
            self.path,
            self.config.get('site', {}).get('output', 'output'))
        self.site = new_module('__main__')
        self.site.__file__ = os.path.join(path, '__init__.py')
        self.site.__path__ = [path]
        with main_module(self.site):
            __import__("__main__.config")
            config = self.site.config.config
            self.registry = config.registry
            self.root = Node(self.registry, path)
            config.set_root_factory(self.root)
            config.add_request_method(static_path)
            config.commit()
            self.registry.settings['config'] = self.config
            self.registry.registerUtility(lambda h, r: h, ITweens)
            self.routes_mapper = config.get_routes_mapper()
            self.traversal_matchers = []
            for route in self.routes_mapper.routelist:
                traversal_preds = [
                    x for x in route.predicates
                    if isinstance(x, TraversePredicate)]
                if not traversal_preds:
                    continue
                matcher = _compile_route(traversal_preds[0].val)[0]
                self.traversal_matchers.append((route, matcher))

    def dispatch(self, path):
        log.debug("dispatch %s" % path)
        for route, matcher in self.traversal_matchers:
            match = matcher(path)
            if match is not None:
                preds = route.predicates
                info = dict(match=match, route=route)
                if preds and not all((p(info, None) for p in preds)):
                    continue
                return info

    def traverse_content(self):
        routes = {}
        for dirpath, dirnames, filenames in os.walk(self.path):
            dirnames[:] = [
                x for x in dirnames
                if (not x.startswith('.')
                    and os.path.join(dirpath, x) != self.outpath)]
            for filename in filenames:
                relpath = os.path.join(dirpath, filename)[self.path_len:].split(os.path.sep)
                info = self.dispatch('/'.join(relpath))
                if info is not None:
                    log.debug("Route:\n%s" % pformat(info))
                    route = info['route']
                    match = info['match']
                    context = traverse(self.root, match['traverse'])['context']
                    context.load()
                    routes.setdefault(route, []).append(match)
        return routes

    def write(self, route_path, response):
        fn = os.path.join(self.outpath, route_path[1:])
        dirname = os.path.dirname(fn)
        if not os.path.lexists(dirname):
            os.makedirs(dirname)
        if os.path.lexists(fn):
            with open(fn, 'rb') as f:
                if f.read() == response.body:
                    log.info("Skipping up to date '%s'." % route_path)
                    return
        log.info("Writing '%s'." % route_path)
        with open(fn, 'wb') as f:
            f.write(response.body)

    def build(self):
        with main_module(self.site):
            visited = set()
            routes = self.traverse_content()
            router = Router(self.registry)
            extensions = self.registry.queryUtility(IRequestExtensions)
            for route in self.routes_mapper.routelist:
                if route in routes:
                    matches = routes[route]
                elif route.factory is not None:
                    matches = route.factory.matches(self.root)
                else:
                    matches = [{}]
                for match in matches:
                    route_path = route.generate(match)
                    if route_path in visited:
                        continue
                    visited.add(route_path)
                    log.debug("Visiting '%s'" % route_path)
                    request = _make_request(route_path, registry=self.registry)
                    request.root_node = self.root
                    if extensions is not None:
                        request._set_extensions(extensions)
                    response = router.handle_request(request)
                    self.write(route_path, response)
