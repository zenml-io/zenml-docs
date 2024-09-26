import os
import re
import argparse

link_pattern = re.compile(
    r"""
    \[(.*?)\]\((.*?)\)                   # Markdown links
    |<a\s+(?:[^>]*?\s+)?href=\"(.*?)\".*?>  # HTML links
    |<([a-zA-Z0-9]+)[^>]*?\s+href=\"(.*?)\"[^>]*?\/?> # General tag with href
    """,
    re.MULTILINE | re.DOTALL | re.VERBOSE,
)


def extract_links(content):
    """Extracts markdown, HTML, and General tags with href links from a given content string."""
    links = []
    for match in link_pattern.finditer(content):
        # Extract markdown links
        md_link_text, md_link_url = match.group(1), match.group(2)
        if md_link_url:
            links.append(("markdown", md_link_text, md_link_url))

        # Extract HTML links
        html_link_url = match.group(3)
        if html_link_url:
            links.append(("html", None, html_link_url))

        # Extract general tag with href links
        tag_name, tag_href_url = match.group(4), match.group(5)
        if tag_name and tag_href_url:
            links.append((tag_name, None, tag_href_url))

    return links


def find_links_in_mdx_files(root_dir, prefix=None):
    """Finds markdown, HTML, and general tag links with href in all .mdx files within a directory recursively."""
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".mdx"):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        links = extract_links(content)
                        if prefix:
                            for link_type, link_text, link_url in links:
                                if (
                                    (
                                        link_type == "markdown"
                                        or link_type == "html"
                                        or link_type
                                    )
                                    and "://" not in link_url  # ignore external links
                                    and not link_url.startswith(
                                        prefix
                                    )  # ignore links that already have the prefix
                                ):
                                    new_link = f"{prefix}{link_url}"
                                    if link_type == "markdown":
                                        content = content.replace(
                                            f"({link_url})", f"({new_link})"
                                        )
                                    elif link_type == "html":
                                        content = re.sub(
                                            r'(href="{})'.format(re.escape(link_url)),
                                            f'href="{new_link}"',
                                            content,
                                        )
                                    else:
                                        content = re.sub(
                                            r'(href="{})'.format(re.escape(link_url)),
                                            f'href="{new_link}"',
                                            content,
                                        )
                            with open(filepath, "w", encoding="utf-8") as f:
                                f.write(content)
                        else:
                            for link_type, link_text, link_url in links:
                                if link_type == "markdown":
                                    print(
                                        f"File: {filepath}\nMarkdown Link: {link_url}\n"
                                    )
                                elif link_type == "html":
                                    print(f"File: {filepath}\nHTML Link: {link_url}\n")
                                else:
                                    print(
                                        f"File: {filepath}\n{link_type} Link: {link_url}\n"
                                    )
                except Exception as e:
                    print(f"Error reading file {filepath}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-directory", type=str, required=True)
    parser.add_argument("--link-prefix", type=str)
    args = parser.parse_args()

    find_links_in_mdx_files(args.root_directory, args.link_prefix)
