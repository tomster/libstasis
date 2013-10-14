from pyramid.decorator import reify
from stasis.entities import IAspects
from stasis.walker import File
from zope.interface import implements
import datetime
import docutils.core
import docutils.writers.html4css1


class RstFile(File):
    @property
    def title(self):
        return self._parts['title']

    @property
    def body(self):
        return self._parts['fragment']

    @reify
    def metadata(self):
        metadata = {}
        for docinfo in self._pub.document.traverse(docutils.nodes.docinfo):
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
                metadata[name] = value
        return metadata

    @reify
    def _pub(self):
        extra_params = {'initial_header_level': '2'}
        pub = docutils.core.Publisher(
            destination_class=docutils.io.StringOutput)
        pub.set_components('standalone', 'restructuredtext', 'html')
        pub.process_programmatic_settings(None, extra_params, None)
        pub.set_source(source_path=self.filepath)
        pub.publish()
        return pub

    @property
    def _parts(self):
        return self._pub.writer.parts


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

    def __iter__(self):
        return iter(['walker', 'date', 'title', 'body'])


def includeme(config):
    if hasattr(config, 'add_walker_file_type'):
        config.add_walker_file_type('.rst', RstFile)
    config.registry.registerAdapter(AspectsForRstFile, (RstFile,), IAspects)
