import pytest

from process_docs_update import (
    is_biggest_version,
    sort_versions,
    process_page,
    process_navigation,
    cleanup_config,
    process_tabs,
    process_anchors,
)


@pytest.fixture
def sample_mint_json():
    return {
        "name": "ZenML",
        "versions": [
            "develop",
            "0.70.0",
            "0.69.0",
            "0.68.0",
            "0.67.0",
            "0.66.0",
            "0.62.0",
            "0.61.0",
        ],
        "navigation": [
            {
                "group": "Getting Started",
                "pages": [
                    "latest/getting-started/introduction",
                    "latest/getting-started/installation",
                    "latest/getting-started/core-concepts",
                    "latest/getting-started/faq",
                ],
                "version": "0.70.0",
            }
        ],
        "tabs": [
            {"name": "Usage", "url": "latest/usage", "version": "0.70.0"},
            {
                "name": "API",
                "url": "latest/api",
                "openapi": "/latest/api/openapi.json",
                "version": "0.70.0",
            },
        ],
        "anchors": [
            {
                "name": "About",
                "icon": "users",
                "url": "https://www.zenml.io",
                "version": "0.70.0",
            }
        ],
    }


def test_is_biggest_version():
    versions = ["0.61.0", "0.62.0", "0.66.0", "0.67.0", "0.68.0", "0.69.0", "0.70.0"]
    assert is_biggest_version("0.71.0", versions)
    assert not is_biggest_version("0.69.0", versions)
    assert not is_biggest_version("develop", versions)  # Changed this assertion
    assert not is_biggest_version("0.60.0", versions)


def test_sort_versions():
    versions = [
        "0.61.0",
        "develop",
        "0.70.0",
        "0.62.0",
        "0.66.0",
        "0.67.0",
        "0.68.0",
        "0.69.0",
    ]
    expected = [
        "develop",
        "0.70.0",
        "0.69.0",
        "0.68.0",
        "0.67.0",
        "0.66.0",
        "0.62.0",
        "0.61.0",
    ]
    assert sort_versions(versions) == expected

    # Test with invalid version
    versions_with_invalid = versions + ["invalid_version"]
    expected_with_invalid = expected + ["invalid_version"]
    assert sort_versions(versions_with_invalid) == expected_with_invalid


def test_process_page():
    assert process_page("index.md", "v/1.0.0") == "v/1.0.0/index.md"
    assert process_page("latest/index.md", "v/1.0.0", "latest") == "v/1.0.0/index.md"

    page_dict = {
        "group": "Getting Started",
        "pages": ["installation.md", "quickstart.md"],
        "icon": "rocket",
    }
    expected = {
        "group": "Getting Started",
        "pages": ["v/1.0.0/installation.md", "v/1.0.0/quickstart.md"],
        "icon": "rocket",
    }
    assert process_page(page_dict, "v/1.0.0") == expected


def test_process_navigation(sample_mint_json):
    source_config = {"navigation": sample_mint_json["navigation"]}
    config = {"navigation": []}
    process_navigation(source_config, config, "v/0.71.0", "0.71.0")
    assert len(config["navigation"]) == 1
    assert config["navigation"][0]["version"] == "0.71.0"
    assert (
        config["navigation"][0]["pages"][0]
        == "v/0.71.0/latest/getting-started/introduction"
    )  # Updated this assertion


def test_cleanup_config(sample_mint_json):
    config = sample_mint_json.copy()
    cleanup_config(config, "0.70.0")
    assert not any(nav["version"] == "0.70.0" for nav in config["navigation"])
    assert not any(tab["version"] == "0.70.0" for tab in config["tabs"])
    assert not any(anchor["version"] == "0.70.0" for anchor in config["anchors"])


def test_process_tabs(sample_mint_json):
    source_config = {"tabs": sample_mint_json["tabs"]}
    config = {"tabs": []}
    process_tabs("0.71.0", "v/0.71.0", source_config, config)
    assert len(config["tabs"]) == 2
    assert config["tabs"][0]["version"] == "0.71.0"
    assert config["tabs"][0]["url"] == "v/0.71.0/latest/usage"  # Updated this assertion
    assert (
        config["tabs"][1]["openapi"] == "/v/0.71.0/latest/api/openapi.json"
    )  # Updated this assertion


def test_process_anchors(sample_mint_json):
    source_config = {"anchors": sample_mint_json["anchors"]}
    config = {"anchors": []}
    process_anchors("0.71.0", source_config, config)
    assert len(config["anchors"]) == 1
    assert config["anchors"][0]["version"] == "0.71.0"


if __name__ == "__main__":
    pytest.main()
