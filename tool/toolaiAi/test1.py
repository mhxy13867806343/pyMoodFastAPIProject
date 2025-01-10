import requests
headers = {
"X-Requested-With":"XMLHttpRequest",
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
}
# 创建一个 Session 对象
session = requests.Session()

# 发起请求，Session 会自动处理 Cookie
response = session.get('https://www.toolai.io',headers=headers)
#['__attrs__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__',
# '__enter__', '__eq__', '__exit__', '__format__', '__ge__', '__getattribute__',
# '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__',
# '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__',
# '__setstate__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 'adapters', 'auth', 'cert',
# 'close', 'cookies', 'delete', 'get', 'get_adapter', 'get_redirect_target', 'head',
# 'headers', 'hooks', 'max_redirects', 'merge_environment_settings', 'mount', 'options',
# 'params', 'patch', 'post', 'prepare_request', 'proxies', 'put', 'rebuild_auth', 'rebuild_method',
# 'rebuild_proxies', 'request', 'resolve_redirects', 'send', 'should_strip_auth', 'stream', 'trust_env', 'verify']

# 查看服务器设置的 Cookie
print(session.headers)