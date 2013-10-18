from zope.interface.registry import Components


class Registry(Components, dict):
    """ convenience class for a component registry that also behaves like a dictionary,
    inspired by the way pyramid creates its own.
    """
