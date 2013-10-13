from zope.interface import Interface


class IConfigFactory(Interface):
    def __call__():
        pass


class INodeFactory(Interface):
    def __call__():
        pass


class IVirtualRootFactory(Interface):
    def __call__():
        pass
