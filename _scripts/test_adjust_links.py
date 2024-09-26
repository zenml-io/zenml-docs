from adjust_links import extract_links, replace_links_with_prefix
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
    <Card title="Example Card" icon="info" href="https://example.com" horizontal/>
    Another card link <Card title="Another Card" icon="star" href="https://example.org" horizontal/>.
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
    And here is a <Card title="Example Card" icon="info" href="https://example.net" horizontal/>.
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


def test_replace_markdown_links():
    content = """
    Here is a [link](/example).
    Another [example](/example-org).
    Another [example](example-org).
    """
    prefix = "/prefix"
    expected_content = """
    Here is a [link](/prefix/example).
    Another [example](/prefix/example-org).
    Another [example](/prefix/example-org).
    """
    assert replace_links_with_prefix(content, prefix) == expected_content


def test_replace_html_links():
    content = """
    Here is an <a href="/example">HTML link</a>.
    Another <a href="/example-org" class="some-class">example</a>.
    Another <a href="example-org" class="some-class">example</a>.
    """
    prefix = "/prefix"
    expected_content = """
    Here is an <a href="/prefix/example">HTML link</a>.
    Another <a href="/prefix/example-org" class="some-class">example</a>.
    Another <a href="/prefix/example-org" class="some-class">example</a>.
    """
    assert replace_links_with_prefix(content, prefix) == expected_content


def test_replace_card_links():
    content = """
    <Card title="Example Card" icon="info" href="/example" horizontal/>
    Another card link <Card title="Another Card" icon="star" href="/example-org" horizontal/>.
    Another card link <Card title="Another Card" icon="star" href="example-org" horizontal/>.
    """
    prefix = "/prefix"
    expected_content = """
    <Card title="Example Card" icon="info" href="/prefix/example" horizontal/>
    Another card link <Card title="Another Card" icon="star" href="/prefix/example-org" horizontal/>.
    Another card link <Card title="Another Card" icon="star" href="/prefix/example-org" horizontal/>.
    """
    assert replace_links_with_prefix(content, prefix) == expected_content


def test_replace_custom_tag_links():
    content = """
    <CustomTag title="Custom Tag" href="/example" />
    Another custom tag <AnotherTag href="/example-org" class="custom-class" />.
    Another custom tag <AnotherTag href="example-org" class="custom-class" />.
    """
    prefix = "/prefix"
    expected_content = """
    <CustomTag title="Custom Tag" href="/prefix/example" />
    Another custom tag <AnotherTag href="/prefix/example-org" class="custom-class" />.
    Another custom tag <AnotherTag href="/prefix/example-org" class="custom-class" />.
    """
    assert replace_links_with_prefix(content, prefix) == expected_content


def test_replace_mixed_links():
    content = """
    Here is a [markdown link](/example).
    And here is an <a href="/example-org">HTML link</a>.
    And here is a <Card title="Example Card" icon="info" href="/example-net" horizontal/>.
    And here is a <CustomTag title="Custom Tag" href="/example-org" />.
    And here is a [example](example-org).
    """
    prefix = "/prefix"
    expected_content = """
    Here is a [markdown link](/prefix/example).
    And here is an <a href="/prefix/example-org">HTML link</a>.
    And here is a <Card title="Example Card" icon="info" href="/prefix/example-net" horizontal/>.
    And here is a <CustomTag title="Custom Tag" href="/prefix/example-org" />.
    And here is a [example](/prefix/example-org).
    """
    assert replace_links_with_prefix(content, prefix) == expected_content


def test_empty_href():
    content = """
    <Card title="Empty Link" href="" />
    <a href="">Empty HTML Link</a>
    [Empty Markdown Link]()
    """
    expected = []
    assert extract_links(content) == expected


def test_whitespace_in_href():
    content = """
    <Card title="Whitespace Link" href=" https://example.com " />
    <a href=" https://example.com ">Whitespace HTML Link</a>
    [Whitespace Markdown Link]( https://example.com )
    """
    expected = [
        ("Card", None, " https://example.com "),
        ("html", None, " https://example.com "),
        ("markdown", "Whitespace Markdown Link", " https://example.com "),
    ]
    assert extract_links(content) == expected


def test_relative_and_absolute_links():
    content = """
    [Relative Link](/relative/path)
    <a href="https://example.com/absolute/path">Absolute Link</a>
    """
    expected = [
        ("markdown", "Relative Link", "/relative/path"),
        ("html", None, "https://example.com/absolute/path"),
    ]
    assert extract_links(content) == expected


def test_links_inside_code_blocks():
    content = """
    ```python
    print("[This is not a link](definitely-not-a-url)")
    ```
    ```mdx
    <ThisIsNotACard href="not-a-url" />
    ```
    [This is a link](/actual-link)
    """
    expected = [
        ("markdown", "This is not a link", "definitely-not-a-url"),
        ("ThisIsNotACard", None, "not-a-url"),
        ("markdown", "This is a link", "/actual-link"),
    ]
    assert extract_links(content) == expected


def test_escaped_characters_markdown():
    content = """
    [Link with \[escaped] characters](https://example.com/escaped)
    """
    expected = [
        ("markdown", "Link with \[escaped] characters", "https://example.com/escaped")
    ]
    assert extract_links(content) == expected


def test_html_entities_in_links():
    content = """
    <a href="https://example.com?param=a&b=c">Link with HTML entities</a>
    """
    expected = [("html", None, "https://example.com?param=a&b=c")]
    assert extract_links(content) == expected


def test_multiline_attributes_in_tags():
    content = """
    <Card title="Multiline Attributes" icon="info"
    href="https://example.com" horizontal/>
    """
    expected = [("Card", None, "https://example.com")]
    assert extract_links(content) == expected


def test_replace_links_with_query_params():
    content = "[Link](/example?param=value)"
    prefix = "/prefix"
    expected = "[Link](/prefix/example?param=value)"
    assert replace_links_with_prefix(content, prefix) == expected


def test_replace_links_with_hash_fragment():
    content = "[Link](/example#section)"
    prefix = "/prefix"
    expected = "[Link](/prefix/example#section)"
    assert replace_links_with_prefix(content, prefix) == expected


def test_replace_links_with_encoded_characters():
    content = "[Link](/example%20with%20spaces)"
    prefix = "/prefix"
    expected = "[Link](/prefix/example%20with%20spaces)"
    assert replace_links_with_prefix(content, prefix) == expected


def test_extract_links_with_encoded_characters():
    content = "[Link](/example%20with%20spaces)"
    expected = [("markdown", "Link", "/example%20with%20spaces")]
    assert extract_links(content) == expected


def test_extract_links_with_query_params():
    content = "[Link](/example?param=value)"
    expected = [("markdown", "Link", "/example?param=value")]
    assert extract_links(content) == expected


def test_extract_links_with_hash_fragment():
    content = "[Link](/example#section)"
    expected = [("markdown", "Link", "/example#section")]
    assert extract_links(content) == expected


# This allows the tests to be run if the script is executed directly.
if __name__ == "__main__":
    pytest.main()
