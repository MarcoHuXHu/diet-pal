# Default Configuration

configs = {
    'server': {
        'host': '127.0.0.1',
        'port': 9000
    },
    'db': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'password': 'password',
        'database': 'diet-pal'
    },
    'session': {
        'cookie_name': 'DietPal',
        'secret': 'jh6iuhbv1',
        'expire': 36
    }
}

class Dict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

# 递归将dict的每一个key-value-pair转换成可以Dict类，其中的__getattr__使得可以用d.x的形式访问
def ToDict(d):
    D = Dict()
    for k, v in d.items():
        if isinstance(v, dict):
            D[k] = ToDict(v)
        else:
            D[k] = v
    return D

configs = ToDict(configs)
