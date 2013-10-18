from pytest import fixture
from libstasis import Registry


@fixture
def registry():
    return Registry()
