"""Unit tests for TLS mode configuration."""

# Standard library
import os
import sys
import types

# Third-party
import pytest


@pytest.mark.fast
def test_tls_mode_system_uses_truststore(monkeypatch):
    import src.validator as v

    v._TLS_CONFIGURED = False
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("CHEM_VALIDATOR_CA_BUNDLE", raising=False)
    monkeypatch.delenv("CHEM_VALIDATOR_TLS_MODE", raising=False)

    truststore_mod = types.SimpleNamespace()
    truststore_mod.called = False

    def inject_into_ssl():
        truststore_mod.called = True

    truststore_mod.inject_into_ssl = inject_into_ssl
    monkeypatch.setitem(sys.modules, "truststore", truststore_mod)

    v._ensure_ca_bundle_configured()
    assert truststore_mod.called is True


@pytest.mark.fast
def test_tls_mode_public_uses_certifi(monkeypatch):
    import src.validator as v

    v._TLS_CONFIGURED = False
    monkeypatch.setenv("CHEM_VALIDATOR_TLS_MODE", "public")
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("CHEM_VALIDATOR_CA_BUNDLE", raising=False)

    truststore_mod = types.SimpleNamespace()
    truststore_mod.called = False

    def inject_into_ssl():
        truststore_mod.called = True

    truststore_mod.inject_into_ssl = inject_into_ssl
    monkeypatch.setitem(sys.modules, "truststore", truststore_mod)

    certifi_mod = types.SimpleNamespace()
    certifi_mod.where = lambda: "/tmp/cafile.pem"
    monkeypatch.setitem(sys.modules, "certifi", certifi_mod)

    v._ensure_ca_bundle_configured()
    assert truststore_mod.called is False
    assert os.environ.get("SSL_CERT_FILE") == "/tmp/cafile.pem"
    assert os.environ.get("REQUESTS_CA_BUNDLE") == "/tmp/cafile.pem"


@pytest.mark.fast
def test_tls_mode_custom_uses_ca_bundle(monkeypatch):
    import src.validator as v

    v._TLS_CONFIGURED = False
    monkeypatch.setenv("CHEM_VALIDATOR_TLS_MODE", "custom")
    monkeypatch.setenv("CHEM_VALIDATOR_CA_BUNDLE", "/tmp/org-ca.pem")
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)

    truststore_mod = types.SimpleNamespace()
    truststore_mod.called = False
    truststore_mod.inject_into_ssl = lambda: setattr(truststore_mod, "called", True)
    monkeypatch.setitem(sys.modules, "truststore", truststore_mod)

    v._ensure_ca_bundle_configured()
    assert truststore_mod.called is False
    assert os.environ.get("SSL_CERT_FILE") == "/tmp/org-ca.pem"
    assert os.environ.get("REQUESTS_CA_BUNDLE") == "/tmp/org-ca.pem"


@pytest.mark.fast
def test_tls_respects_existing_ssl_cert_file(monkeypatch):
    import src.validator as v

    v._TLS_CONFIGURED = False
    monkeypatch.setenv("SSL_CERT_FILE", "/tmp/already-set.pem")
    monkeypatch.setenv("CHEM_VALIDATOR_TLS_MODE", "public")

    truststore_mod = types.SimpleNamespace()
    truststore_mod.called = False
    truststore_mod.inject_into_ssl = lambda: setattr(truststore_mod, "called", True)
    monkeypatch.setitem(sys.modules, "truststore", truststore_mod)

    v._ensure_ca_bundle_configured()
    assert truststore_mod.called is False
    assert os.environ.get("SSL_CERT_FILE") == "/tmp/already-set.pem"
