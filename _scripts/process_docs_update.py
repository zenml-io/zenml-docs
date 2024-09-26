import argparse
import json
import os
import zipfile
import shutil
import copy
from typing import List, Dict, Union, Optional, Any
from packaging import version


def is_biggest_version(version: str, versions: List[str]) -> bool:
    """
    Check if the given version is the biggest version.

    Args:
        version: The version to check.
        versions: The list of versions to compare against.

    Returns:
        True if the version is the biggest version, False otherwise.
    """
    versions.append(version)
    sorted_versions = sort_versions(versions)
    sorted_versions = [v for v in sorted_versions if v != "develop"]
    return version == sorted_versions[0]


def sort_versions(versions: List[str]) -> List[str]:
    """
    Sort the given list of versions in descending order.

    Args:
        versions: The list of versions to sort.

    Returns:
        A sorted list of versions in descending order.
    """

    def version_key(v: str) -> tuple:
        if v == "develop":
            return (version.parse("99999.99999.99999"), v)
        try:
            return (version.parse(v), v)
        except version.InvalidVersion:
            return (version.parse("0.0.0"), v)

    sorted_versions = sorted(versions, key=version_key)

    if "develop" in sorted_versions:
        develop_index = sorted_versions.index("develop")
        if develop_index != len(sorted_versions) - 1:
            sorted_versions.insert(-1, sorted_versions.pop(develop_index))

    return list(reversed(sorted_versions))


def get_latest_version(versions: List[str]) -> Optional[str]:
    """
    Get the latest version from the list of versions.

    Args:
        versions: The list of versions.

    Returns:
        The latest version, or None if no versions are available.
    """
    l = [v for v in versions if v != "develop"]
    return l[0] if l else None


def is_latest_version(version: str, versions: List[str]) -> bool:
    """
    Check if the given version is the latest version.

    Args:
        version: The version to check.
        versions: The list of versions.

    Returns:
        True if the version is the latest version, False otherwise.
    """
    return version == get_latest_version(versions)


def extract_files(destination_path_prefix: str) -> None:
    """
    Extract files from the zip archive and copy them to the destination path prefix.

    Args:
        destination_path_prefix: The destination path prefix.
    """
    os.makedirs("temp_docs", exist_ok=True)
    for root, _, files in os.walk("temp_docs"):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, "temp_docs")

            if relative_path.startswith("README.md") or relative_path.startswith(
                "_assets/"
            ):
                dest_path = relative_path
            else:
                dest_path = os.path.join(destination_path_prefix, relative_path)

            dir_name = os.path.dirname(dest_path)

            if dir_name != "" and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)

            shutil.copy2(file_path, dest_path)


def process_navigation(
    source_config: Dict[str, Any],
    config: Dict[str, Any],
    destination_path_prefix: str,
    version: str,
) -> None:
    """
    Process the navigation to include the version in their paths.

    Args:
        source_config: The source configuration.
        config: The configuration to process.
        destination_path_prefix: The destination path prefix.
        version: The version to include in the paths.
    """
    if "navigation" not in source_config:
        raise Exception("No navigation found in source config")

    new_groups = []
    for group in source_config["navigation"]:
        new_group = copy.deepcopy(group)
        new_group["pages"] = [
            process_page(page, destination_path_prefix) for page in new_group["pages"]
        ]
        new_group["version"] = version
        new_groups.append(new_group)
    config["navigation"] = new_groups + config["navigation"]


def process_page(
    page: Union[str, Dict[str, Any]],
    destination_path_prefix: str,
    replace_version: Optional[str] = None,
) -> Union[str, Dict[str, Any]]:
    """
    Recursively process a page or group of pages.

    Args:
        page: The page or group of pages to process.
        destination_path_prefix: The destination path prefix.
        replace_version: The version to replace, if any.

    Returns:
        The processed page or group of pages with versioned paths.
    """
    if isinstance(page, str):
        if replace_version and page.startswith(replace_version):
            page = page.removeprefix(replace_version + "/")
        return f"{destination_path_prefix}/{page}"
    elif isinstance(page, dict):
        result = {
            "group": page["group"],
            "pages": [
                process_page(p, destination_path_prefix, replace_version)
                for p in page["pages"]
            ],
        }
        if "icon" in page:
            result["icon"] = page["icon"]
        if "iconType" in page:
            result["iconType"] = page["iconType"]
        return result
    else:
        return page


def copy_directory(source_path_prefix: str, destination_path_prefix: str) -> None:
    """
    Copy the directory from the source path prefix to the destination path prefix.

    Args:
        source_path_prefix: The source path prefix.
        destination_path_prefix: The destination path prefix.
    """
    shutil.copytree(source_path_prefix, destination_path_prefix)


def copy_config(config: Dict[str, Any], source_version: str) -> None:
    """
    Copy the navigation from the source version.

    Args:
        config: The configuration to copy the navigation from.
        source_version: The source version.
    """
    new_groups = []
    for nav in config["navigation"]:
        new_group = copy.deepcopy(nav)
        if nav["version"] == source_version:
            new_group["pages"] = [
                process_page(page, f"v/{source_version}", "latest")
                for page in new_group["pages"]
            ]
        new_groups.append(new_group)
    config["navigation"] = new_groups

    for tab in config["tabs"]:
        if "openapi" in tab:
            if tab["openapi"].startswith("/latest"):
                tab["openapi"] = tab["openapi"].removeprefix("/latest")
                tab["openapi"] = f"/v/{source_version}{tab['openapi']}"
        if tab["url"].startswith("latest"):
            tab["url"] = tab["url"].removeprefix("latest")
            tab["url"] = f"/v/{source_version}{tab['url']}"


def cleanup_directory(destination_path_prefix: str) -> None:
    """
    Clean up the directory for the given destination path prefix.

    Args:
        destination_path_prefix: The destination path prefix.
    """
    shutil.rmtree(destination_path_prefix, ignore_errors=True)


def cleanup_config(config: Dict[str, Any], version: str) -> None:
    """
    Delete all entries in the navigation that are in the version.

    Args:
        config: The configuration to clean up.
        version: The version to clean up.
    """
    config["navigation"] = [
        nav for nav in config["navigation"] if nav["version"] != version
    ]
    config["tabs"] = [tab for tab in config["tabs"] if tab["version"] != version]
    config["anchors"] = [
        anchor for anchor in config["anchors"] if anchor["version"] != version
    ]


def process_tabs(
    version: str,
    destination_path_prefix: str,
    source_config: Dict[str, Any],
    config: Dict[str, Any],
) -> None:
    """
    Process the tabs for the given version.

    Args:
        version: The version to process.
        destination_path_prefix: The destination path prefix.
        source_config: The source configuration.
        config: The configuration to process.
    """
    if "tabs" in source_config:
        for tab in source_config["tabs"]:
            if "openapi" in tab:
                tab["openapi"] = f"/{destination_path_prefix}{tab['openapi']}"
            tab["url"] = f"{destination_path_prefix}/{tab['url']}"
            tab["version"] = version
            config["tabs"].append(tab)


def process_anchors(
    version: str, source_config: Dict[str, Any], config: Dict[str, Any]
) -> None:
    """
    Process the anchors for the given version.

    Args:
        version: The version to process.
        source_config: The source configuration.
        config: The configuration to process.
    """
    if "anchors" in source_config:
        for anchor in source_config["anchors"]:
            anchor["version"] = version
            config["anchors"].append(anchor)


def process_docs_update(version: str) -> None:
    """
    Process the documentation update for a given version.

    Args:
        version: The version to process.
    """
    with zipfile.ZipFile("docs_data.zip", "r") as zip_ref:
        zip_ref.extractall("temp_docs")

    source_mint_json = os.path.join("temp_docs", "mint.json")
    dest_mint_json = "mint.json"

    with open(source_mint_json, "r") as f:
        source_config = json.load(f)

    if os.path.exists(dest_mint_json):
        with open(dest_mint_json, "r") as f:
            config = json.load(f)
    else:
        config = copy.deepcopy(source_config)
        config["navigation"] = []
        config["tabs"] = []
        config["anchors"] = []
        config["versions"] = []

    if version == "develop":
        destination_path_prefix = version
        if version in config["versions"]:
            cleanup_directory(destination_path_prefix)
            cleanup_config(config, version)
        else:
            config["versions"].insert(0, version)

        # add destination_path_prefix
    elif version in config["versions"]:
        print(f"Processing old version: {version}")
        if is_latest_version(version, config["versions"]):
            destination_path_prefix = "latest"
        else:
            destination_path_prefix = f"v/{version}"

        cleanup_directory(destination_path_prefix)
        cleanup_config(config, version)

        # add destination_path_prefix
    elif version not in config["versions"]:
        if is_biggest_version(version, copy.deepcopy(config["versions"])):
            destination_path_prefix = "latest"
            latest_version = get_latest_version(config["versions"])
            print(f"Latest version: {latest_version}")
            if latest_version:
                copy_directory("latest", f"v/{latest_version}")
                copy_config(config, latest_version)
                # replace "latest" with v/{latest_version}
            # add destination_path_prefix
        else:
            destination_path_prefix = f"v/{version}"
            # add destination_path_prefix

        config["versions"].insert(0, version)

    extract_files(destination_path_prefix)
    process_navigation(source_config, config, destination_path_prefix, version)
    process_anchors(version, source_config, config)
    process_tabs(version, destination_path_prefix, source_config, config)

    config["versions"] = sort_versions(config["versions"])

    a = [
        n
        for n in config["navigation"]
        if n["version"] == get_latest_version(config["versions"])
    ]
    b = [
        n
        for n in config["navigation"]
        if n["version"] != get_latest_version(config["versions"])
    ]
    config["navigation"] = a + b

    with open(dest_mint_json, "w") as f:
        json.dump(config, f, indent=2)

    shutil.rmtree("temp_docs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ZenML docs update")
    parser.add_argument("--version", required=True, help="Version to sync")

    args = parser.parse_args()
    process_docs_update(args.version)
