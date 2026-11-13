"""ensure_superuser: the admin account comes from environment variables at deploy."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_creates_superuser_from_env(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "admin")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "s3cret-pass")
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
    call_command("ensure_superuser")
    user = User.objects.get(username="admin")
    assert user.is_superuser and user.is_staff
    assert user.check_password("s3cret-pass")


def test_rerun_updates_password_without_duplicating(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "admin")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "first-pass")
    call_command("ensure_superuser")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "second-pass")
    call_command("ensure_superuser")
    assert User.objects.filter(username="admin").count() == 1
    assert User.objects.get(username="admin").check_password("second-pass")


def test_skips_when_not_configured(monkeypatch, capsys):
    monkeypatch.delenv("DJANGO_SUPERUSER_USERNAME", raising=False)
    monkeypatch.delenv("DJANGO_SUPERUSER_PASSWORD", raising=False)
    call_command("ensure_superuser")
    assert User.objects.count() == 0
    assert "skipping" in capsys.readouterr().out


def test_half_configured_is_an_error(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "admin")
    monkeypatch.delenv("DJANGO_SUPERUSER_PASSWORD", raising=False)
    with pytest.raises(CommandError):
        call_command("ensure_superuser")


def test_demo_prefix_rejected(monkeypatch):
    """cleanup_demo deletes demo_ users, so the admin must never use that prefix."""
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "demo_admin")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "x-pass")
    with pytest.raises(CommandError):
        call_command("ensure_superuser")
