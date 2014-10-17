__author__ = 'anzigly'

"""Unit test for `virtman.wsgi`"""

import mock
import os.path
import tempfile
import urllib2

from oslo.config import cfg
import testtools
import webob
import webob.dec

from virtman.common import exception
from virtman.openstack.common import gettextutils
from virtman import test
from virtman.common import wsgi

CONF = cfg.CONF

TEST_VAR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                               'var'))

class TestLoaderNothingExists(test.TestCase):
    """Loader tests where os.path.exists always returns False."""

    def setUp(self):
        super(TestLoaderNothingExists, self).setUp()
        self.stubs.Set(os.path, 'exists', lambda _: False)

    def test_config_not_found(self):
        self.assertRaises(
            exception.ConfigNotFound,
            wsgi.Loader,
        )


class TestLoaderNormalFilesystem(test.TestCase):
    """Loader tests with normal filesystem (unmodified os.path module)."""

    _paste_config = """
[app:test_app]
use = egg:Paste#static
document_root = /tmp
    """

    def setUp(self):
        super(TestLoaderNormalFilesystem, self).setUp()
        self.config = tempfile.NamedTemporaryFile(mode="w+t")
        self.config.write(self._paste_config.lstrip())
        self.config.seek(0)
        self.config.flush()
        self.loader = wsgi.Loader(self.config.name)
        self.addCleanup(self.config.close)

    def test_config_found(self):
        self.assertEqual(self.config.name, self.loader.config_path)

    def test_app_not_found(self):
        self.assertRaises(
            exception.PasteAppNotFound,
            self.loader.load_app,
            "non-existent app",
        )

    def test_app_found(self):
        url_parser = self.loader.load_app("test_app")
        self.assertEqual("/tmp", url_parser.directory)


class TestWSGIServer(test.TestCase):
    """WSGI server tests."""
    def _ipv6_configured():
        try:
            with file('/proc/net/if_inet6') as f:
                return len(f.read()) > 0
        except IOError:
            return False

    def test_no_app(self):
        server = wsgi.Server("test_app", None)
        self.assertEqual("test_app", server.name)

    def test_start_random_port(self):
        server = wsgi.Server("test_random_port", None, host="127.0.0.1")
        self.assertEqual(0, server.port)
        server.start()
        self.assertNotEqual(0, server.port)
        server.stop()
        server.wait()

    @testtools.skipIf(not _ipv6_configured(),
                      "Test requires an IPV6 configured interface")
    def test_start_random_port_with_ipv6(self):
        server = wsgi.Server("test_random_port",
                                    None,
                                    host="::1")
        server.start()
        self.assertEqual("::1", server.host)
        self.assertNotEqual(0, server.port)
        server.stop()
        server.wait()

    def test_app(self):
        greetings = 'Hello, World!!!'

        def hello_world(env, start_response):
            if env['PATH_INFO'] != '/':
                start_response('404 Not Found',
                               [('Content-Type', 'text/plain')])
                return ['Not Found\r\n']
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return [greetings]

        server = wsgi.Server("test_app", hello_world)
        server.start()

        response = urllib2.urlopen('http://127.0.0.1:%d/' % server.port)
        self.assertEqual(greetings, response.read())

        server.stop()

    def test_app_using_ssl(self):
        CONF.set_default("ssl_cert_file",
                         os.path.join(TEST_VAR_DIR, 'certificate.crt'))
        CONF.set_default("ssl_key_file",
                         os.path.join(TEST_VAR_DIR, 'privatekey.key'))

        greetings = 'Hello, World!!!'

        @webob.dec.wsgify
        def hello_world(req):
            return greetings

        server = wsgi.Server("test_app", hello_world)
        server.start()

        response = urllib2.urlopen('https://127.0.0.1:%d/' % server.port)
        self.assertEqual(greetings, response.read())

        server.stop()

    @testtools.skipIf(not _ipv6_configured(),
                      "Test requires an IPV6 configured interface")
    def test_app_using_ipv6_and_ssl(self):
        CONF.set_default("ssl_cert_file",
                         os.path.join(TEST_VAR_DIR, 'certificate.crt'))
        CONF.set_default("ssl_key_file",
                         os.path.join(TEST_VAR_DIR, 'privatekey.key'))

        greetings = 'Hello, World!!!'

        @webob.dec.wsgify
        def hello_world(req):
            return greetings

        server = wsgi.Server("test_app",
                                    hello_world,
                                    host="::1",
                                    port=0)
        server.start()

        response = urllib2.urlopen('https://[::1]:%d/' % server.port)
        self.assertEqual(greetings, response.read())

        server.stop()