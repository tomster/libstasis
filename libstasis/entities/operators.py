from types import FunctionType

for _name, _obj in vars(__import__('sqlalchemy.sql.operators')).items():
    if isinstance(_obj, FunctionType):
        globals()[_name] = _obj

del _name, _obj, FunctionType
