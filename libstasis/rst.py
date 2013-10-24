from propdict import propdict
from libstasis.entities import IAspects
from zope.interface import implements
import datetime
import docutils.core
import docutils.writers.html4css1


class RstFile(propdict):

    @property
    def title(self):
        return self._parts()['title']

    @property
    def body(self):
        return self._parts().get('fragment')

    @property
    def metadata(self):
        if hasattr(self, '_metadata'):
            return self._metadata
        self._metadata = {}
        for docinfo in self.pub().document.traverse(docutils.nodes.docinfo):
            for element in docinfo.children:
                if element.tagname == 'field':
                    name_elem, body_elem = element.children
                    name = name_elem.astext()
                    value = body_elem.astext()
                else:
                    name = element.tagname
                    value = element.astext()
                name = name.lower()
                if name == 'date':
                    value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M")
                self._metadata[name] = value
        return self._metadata

    def pub(self):
        # caching
        if hasattr(self, '_pub'):
            return self._pub
        extra_params = {'initial_header_level': '2'}
        _pub = docutils.core.Publisher(
            destination_class=docutils.io.StringOutput)
        _pub.set_components('standalone', 'restructuredtext', 'html')
        _pub.process_programmatic_settings(None, extra_params, None)
        _pub.set_source(source_path=self.file.filepath)
        _pub.publish()
        self._pub = _pub
        return _pub

    def _parts(self):
        return self.pub().writer.parts

    def __init__(self, file=None):
        if file is not None:
            self.file = file


class AspectsForRstFile(object):
    implements(IAspects)

    def __init__(self, rstfile):
        self.rstfile = rstfile

    def __getitem__(self, aspect):
        if aspect == 'walker':
            return self.rstfile.walker
        elif aspect == 'date':
            return self.rstfile.metadata['date']
        elif aspect == 'title':
            return self.rstfile.title
        elif aspect == 'body':
            return self.rstfile.body
        raise KeyError(aspect)

    def keys(self):
        return ['walker', 'date', 'title', 'body']

    def __iter__(self):
        return iter(self.keys())


def includeme(config):
    if hasattr(config, 'add_walker_file_type'):
        config.add_walker_file_type('.rst', RstFile)
    config.registry.registerAdapter(AspectsForRstFile, (RstFile,), IAspects)
