import json

BASE_TYPES = (str, int, float, list, tuple, dict, bool)
KEY_TYPES = (str, int, float, tuple, bool)


def to_arg(type_, value):
    if type_ in BASE_TYPES:
        if value is None:
            return type_()
        return type_(value)
    else:
        if isinstance(type_, type):
            return unmarshal(value, type_)
        else:
            if isinstance(type_, list):
                if value is None:
                    return None
                assert isinstance(value, list)
                assert len(type_) == 1
                sub_type = type_[0]

                list_values = []
                if sub_type in BASE_TYPES:
                    for v in value:
                        if v is None:
                            list_values.append(None)
                        else:
                            list_values.append(sub_type(v))
                elif sub_type is object:
                    for v in value:
                        list_values.append(v)
                elif isinstance(sub_type, (list, dict)):  # 列表里面是列表 比如: [[str]], 列表里面是字典 比如: [{str:str}]
                    for v in value:
                        list_values.append(to_arg(sub_type, v))
                else:
                    for v in value:
                        list_values.append(unmarshal(v, sub_type))
                return list_values
            elif isinstance(type_, dict):
                if value is None:
                    return None
                assert isinstance(value, dict)
                assert len(type_) == 1
                key_type = list(type_.keys())[0]
                assert key_type in KEY_TYPES
                value_type = list(type_.values())[0]
                dict_value = {}
                if value_type in BASE_TYPES:
                    for k, v in value.items():
                        if v is None:
                            dict_value[key_type(k)] = None
                        else:
                            dict_value[key_type(k)] = value_type(v)
                elif value_type is object:
                    for k, v in value.items():
                        dict_value[key_type(k)] = v
                else:
                    for k, v in value.items():
                        dict_value[key_type(k)] = unmarshal(v, value_type)
                return dict_value


def unmarshal(json_, type_: type):
    if json_ is None:
        return None

    if not hasattr(type_.__init__, "__annotations__"):
        raise Exception(f"{type_} need `__init__` method")

    init_func_annotations = type_.__init__.__annotations__

    if isinstance(json_, (str, bytes)):
        json_dict = json.loads(json_)
    elif isinstance(json_, dict):
        json_dict = json_
    else:
        raise Exception("only support `str` or `dict` type for `json_`")

    kwargs = {}
    for k, v in init_func_annotations.items():
        value = json_dict.get(k)
        if value is not None:
            kwargs[k] = to_arg(v, value)

    return type_(**kwargs)


def marshal_to_dict(obj) -> dict:
    # 这个 obj 必须是 自定义类型
    if type(obj) in BASE_TYPES:
        raise Exception("obj must be custom class type")
    # 自行已类型必须有 __init__ 方法
    if not hasattr(obj.__init__, "__annotations__"):
        raise Exception(f"{type(obj)} need `__init__` method")

    init_func_annotations = obj.__init__.__annotations__

    dict_ = {}
    # 要格参与序列化的参数必须在 __init__中出现
    for k, v in init_func_annotations.items():
        value = obj.__getattribute__(k)
        if v in BASE_TYPES:
            dict_[k] = v(value)
        else:
            if isinstance(v, type):
                # 自定义类型
                dict_[k] = marshal_to_dict(value)
            else:
                # todo 其他 [str] {str:str} ...
                pass

    return dict_


def marshal(obj) -> str:
    return json.dumps(marshal_to_dict(obj))
