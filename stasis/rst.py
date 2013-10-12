from stasis.core import Node
import datetime
import docutils.core
import docutils.writers.html4css1


class RstNode(Node):
    def load(self):
        extra_params = {'initial_header_level': '2'}
        pub = docutils.core.Publisher(
            destination_class=docutils.io.StringOutput)
        pub.set_components('standalone', 'restructuredtext', 'html')
        pub.process_programmatic_settings(None, extra_params, None)
        pub.set_source(source_path=self.path)
        pub.publish()
        parts = pub.writer.parts
        self.title = parts['title']
        self.body = parts['fragment']
        self.metadata = {}
        for docinfo in pub.document.traverse(docutils.nodes.docinfo):
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
                self.metadata[name] = value


def includeme(config):
    config.add_node_factory('.rst', RstNode)
