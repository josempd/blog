"""Unit tests for app.content.slugify."""

from app.content import slugify


def test_basic_ascii_text() -> None:
    assert slugify("Hello World") == "hello-world"


def test_lowercase_conversion() -> None:
    assert slugify("FastAPI Blog") == "fastapi-blog"


def test_accent_stripping_cafe() -> None:
    assert slugify("café") == "cafe"


def test_accent_stripping_multiple() -> None:
    assert slugify("Ångström über naïve résumé") == "angstrom-uber-naive-resume"


def test_numbers_preserved() -> None:
    assert slugify("Python 3.10 release") == "python-3-10-release"


def test_multiple_hyphens_collapse() -> None:
    assert slugify("foo---bar") == "foo-bar"


def test_special_chars_become_hyphens() -> None:
    assert slugify("hello, world!") == "hello-world"


def test_leading_hyphens_stripped() -> None:
    assert slugify("---hello") == "hello"


def test_trailing_hyphens_stripped() -> None:
    assert slugify("hello---") == "hello"


def test_leading_and_trailing_hyphens_stripped() -> None:
    assert slugify("   hello world   ") == "hello-world"


def test_empty_string() -> None:
    assert slugify("") == ""


def test_only_special_chars() -> None:
    assert slugify("!@#$%") == ""


def test_already_valid_slug() -> None:
    assert slugify("my-post-slug") == "my-post-slug"


def test_mixed_unicode_and_ascii() -> None:
    assert slugify("Héllo Wörld") == "hello-world"


def test_underscore_becomes_hyphen() -> None:
    assert slugify("hello_world") == "hello-world"
