from zope.interface import Interface


class INodeFactory(Interface):
    def __call__():
        pass
