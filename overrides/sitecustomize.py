from curl_cffi import requests as _curl_requests

_orig_async_session_init = _curl_requests.AsyncSession.__init__


def _async_session_init(self, *args, impersonate=None, **kwargs):
    return _orig_async_session_init(self, *args, **kwargs)


_curl_requests.AsyncSession.__init__ = _async_session_init
