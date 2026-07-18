"""Tests for HTTPS transport configuration."""

import ssl

from musicscope.utils.http import trusted_ssl_context


def test_http_uses_a_verifying_ssl_context() -> None:
    context = trusted_ssl_context()

    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname
