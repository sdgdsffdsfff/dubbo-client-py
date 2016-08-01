# coding=utf-8
import random
from urllib2 import HTTPError

from pyjsonrpc import HttpClient, JsonRpcError

from dubbo_client.registry import Registry
from dubbo_client.rpcerror import NoProvider, ConnectionFail, dubbo_client_errors, InternalError, DubboClientError

__author__ = 'caozupeng'


class DubboClient(object):
    interface = ''
    group = ''
    version = ''

    class _Method(object):

        def __init__(self, client_instance, method):
            self.client_instance = client_instance
            self.method = method

        def __call__(self, *args, **kwargs):
            return self.client_instance.call(self.method, *args, **kwargs)

    def __init__(self, interface, registry, **kwargs):
        assert isinstance(registry, Registry)
        self.interface = interface
        self.registry = registry
        self.group = kwargs.get('group', '')
        self.version = kwargs.get('version', '')
        self.registry.subscribe(interface)
        self.registry.register(interface)

    def call(self, method, *args, **kwargs):
        provides = self.registry.get_provides(self.interface, version=self.version, group=self.group)
        if len(provides) == 0:
            raise NoProvider('can not find provide', self.interface)
        ip_port, service_url = random.choice(provides.items())
        # print service_url.location
        client = HttpClient(url="http://{0}{1}".format(ip_port, service_url.path))
        try:
            return client.call(method, *args, **kwargs)
        except HTTPError, e:
            raise ConnectionFail(None, e.filename)
        except JsonRpcError, error:
            if error.code in dubbo_client_errors:
                raise dubbo_client_errors[error.code](message=error.message, data=error.data)
            else:
                raise DubboClientError(code=error.code, message=error.message, data=error.data)
        except Exception, ue:
            if hasattr(ue, 'reason'):
                raise InternalError(ue.message, ue.reason)
            else:
                raise InternalError(ue.message, None)

    def __call__(self, method, *args, **kwargs):
        """
        Redirects the direct call to *self.call*
        """
        return self.call(method, *args, **kwargs)

    def __getattr__(self, method):
        """
        Allows the usage of attributes as *method* names.
        """
        return self._Method(client_instance=self, method=method)


if __name__ == '__main__':
    pass
