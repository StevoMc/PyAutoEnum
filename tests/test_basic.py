"""
PyAutoEnum test suite.
"""

import unittest

import pytest


class TestPyAutoEnum(unittest.TestCase):
    """Basic test cases for PyAutoEnum."""
    
    def test_import(self):
        """Test that the package can be imported."""
        try:
            import pyautoenum
            self.assertIsNotNone(pyautoenum.__version__)
        except ImportError:
            self.fail("Failed to import pyautoenum package")


def test_is_ip_address():
    """Test the is_ip_address function."""
    from pyautoenum.utils.network import is_ip_address
    
    assert is_ip_address("192.168.1.1") is True
    assert is_ip_address("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
    assert is_ip_address("example.com") is False
    assert is_ip_address("256.256.256.256") is False
    assert is_ip_address("") is False


def test_get_hostname_from_url():
    """Test the get_hostname_from_url function."""
    from pyautoenum.utils.network import get_hostname_from_url
    
    assert get_hostname_from_url("https://example.com/path") == "example.com"
    assert get_hostname_from_url("http://subdomain.example.com:8080") == "subdomain.example.com"
    assert get_hostname_from_url("invalid") is None
