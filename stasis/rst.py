from pyramid.decorator import reify
from stasis.node import Node
import datetime
import docutils.core
import docutils.writers.html4css1


class RstNode(Node):
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
        pub.set_source(source_path=self.abspath)
        pub.publish()
        return pub

    @property
    def _parts(self):
        return self._pub.writer.parts


def includeme(config):
    config.add_node_factory('.rst', RstNode)
