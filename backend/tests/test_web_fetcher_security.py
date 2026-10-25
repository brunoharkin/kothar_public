import pytest

from backend.core.web_fetcher import is_safe_url


@pytest.mark.parametrize("url", [
    "http://github.com/openai",
    "https://github.com.evil.invalid/x",
    "https://evilgithub.com/x",
    "https://localhost/admin",
    "https://user:pass@github.com/x",
])
def test_unsafe_fetch_targets_are_rejected(url):
    assert not is_safe_url(url)


def test_exact_or_subdomain_allowlist_is_accepted():
    assert is_safe_url("https://github.com/openai")
    assert is_safe_url("https://docs.python.org/3/")
