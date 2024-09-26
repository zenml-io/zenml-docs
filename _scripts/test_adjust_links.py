from adjust_links import extract_links
import pytest


def test_markdown_links():
    content = """
    Here is a [link](https://example.com).
    Another [example](https://example.org).
    """
    expected = [
        ("markdown", "link", "https://example.com"),
        ("markdown", "example", "https://example.org"),
    ]
    assert extract_links(content) == expected


def test_html_links():
    content = """
    Here is an <a href="https://example.com">HTML link</a>.
    Another <a href="https://example.org" class="some-class">example</a>.
    """
    expected = [
        ("html", None, "https://example.com"),
        ("html", None, "https://example.org"),
    ]
    assert extract_links(content) == expected


def test_card_links():
    content = """
    <Card title="Example Card" icon="info" href="https://example.com" horizontal />
    Another card link <Card title="Another Card" icon="star" href="https://example.org" horizontal />.
    """
    expected = [
        ("Card", None, "https://example.com"),
        ("Card", None, "https://example.org"),
    ]
    assert extract_links(content) == expected


def test_custom_tag_links():
    content = """
    <CustomTag title="Custom Tag" href="https://example.com" />
    Another custom tag <AnotherTag href="https://example.org" class="custom-class" />.
    """
    expected = [
        ("CustomTag", None, "https://example.com"),
        ("AnotherTag", None, "https://example.org"),
    ]
    assert extract_links(content) == expected


def test_mixed_links():
    content = """
    Here is a [markdown link](https://example.com).
    And here is an <a href="https://example.org">HTML link</a>.
    And here is a <Card title="Example Card" icon="info" href="https://example.net" horizontal />.
    And here is a <CustomTag title="Custom Tag" href="https://example.org" />.
    """
    expected = [
        ("markdown", "markdown link", "https://example.com"),
        ("html", None, "https://example.org"),
        ("Card", None, "https://example.net"),
        ("CustomTag", None, "https://example.org"),
    ]
    assert extract_links(content) == expected


def test_links_with_newlines():
    content = """
    Here is a markdown link with a newline:
    [link
    text](https://example.com).
    
    Another markdown link:
    [another
    example](https://example.org).

    Another markdown link:
    [another
    example](
    https://example.org).

    Another markdown link:
    [anotherexample](https://example
    .org).
    """
    expected = [
        ("markdown", "link\n    text", "https://example.com"),
        ("markdown", "another\n    example", "https://example.org"),
        ("markdown", "another\n    example", "\n    https://example.org"),
        ("markdown", "anotherexample", "https://example\n    .org"),
    ]
    assert extract_links(content) == expected


def test_no_links():
    content = """
    Just some random text with no actual links.
    """
    expected = []
    assert extract_links(content) == expected


def test_invalid_markdown_links():
    content = """
    Here is an invalid markdown link [example](invalid.
    [This one](valid-url.
    no closing parenthesis

    Another one with no closing parenthesis: [another link](https://example.com
    """
    expected = []
    assert extract_links(content) == expected


def test_invalid_html_links():
    content = """
    Here is an invalid HTML link <a href=https://example.com">missing quote</a>.
    Another one <a>https://example.org</a> with no href attribute.
    """
    expected = []
    assert extract_links(content) == expected


def test_general_invalid_tags():
    content = """
    Here is an invalid custom tag <CustomTag href=https://example.com">missing quote</CustomTag>.
    Another invalid tag <AnotherTag>https://example.org</AnotherTag> without href attribute.
    """
    expected = []
    assert extract_links(content) == expected


# This allows the tests to be run if the script is executed directly.
if __name__ == "__main__":
    pytest.main()
