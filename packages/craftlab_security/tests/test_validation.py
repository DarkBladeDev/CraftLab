import os
import pytest
from craftlab_security.validation import validate_production_security_environment


def test_validation_dev_mode_permits_defaults(monkeypatch):
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("CRAFTLAB_AUTH_ENABLED", "false")
    monkeypatch.setenv("CRAFTLAB_ROOT_KEY", "change_me_to_a_secure_root_token")
    # Should not raise in development
    validate_production_security_environment()


def test_validation_prod_mode_aborts_on_auth_disabled(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("CRAFTLAB_AUTH_ENABLED", "false")
    monkeypatch.setenv("CRAFTLAB_ROOT_KEY", "my_secure_prod_key_12345")
    with pytest.raises(RuntimeError, match="Production mode forbids CRAFTLAB_AUTH_ENABLED=false"):
        validate_production_security_environment()


def test_validation_prod_mode_aborts_on_default_root_key(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("CRAFTLAB_AUTH_ENABLED", "true")
    monkeypatch.setenv("CRAFTLAB_ROOT_KEY", "change_me_to_a_secure_root_token")
    with pytest.raises(RuntimeError, match="Production mode requires a secure"):
        validate_production_security_environment()


def test_validation_prod_mode_succeeds_on_valid_config(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("CRAFTLAB_AUTH_ENABLED", "true")
    monkeypatch.setenv("CRAFTLAB_ROOT_KEY", "a_very_strong_random_secret_token_98765")
    validate_production_security_environment()
