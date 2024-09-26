import os
import re

import re
import pytest

link_pattern = re.compile(
    r"\[(.*?)\]\((.*?)\)|<a\s+(?:[^>]*?\s+)?href=\"(.*?)\"(?:\s+[^>]*?)?>", re.MULTILINE | re.DOTALL
)

def extract_links(content):
    """Extracts markdown and HTML links from a given content string."""
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

    return links

def find_links_in_mdx_files(root_dir):
    """Finds markdown and HTML links in all .mdx files within a directory recursively."""
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".mdx"):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        links = extract_links(content)
                        for link_type, link_text, link_url in links:
                            if link_type == "markdown":
                                print(f"File: {filepath}\nMarkdown Link: {link_url}\n")
                            elif link_type == "html":
                                print(f"File: {filepath}\nHTML Link: {link_url}\n")
                except Exception as e:
                    print(f"Error reading file {filepath}: {e}")

if __name__ == "__main__":
    root_directory = "."  # Specify your root directory
    find_links_in_mdx_files(root_directory)