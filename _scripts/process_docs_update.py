import argparse
import json
import os
import zipfile
import shutil
import copy


def get_latest_version(versions):
    """
    Get the latest version from the list of versions.

    Args:
        versions (list): The list of versions.

    Returns:
        str: The latest version.
    """
    return versions[0] if versions else None


def is_latest_version(version, versions):
    """
    Check if the version is the latest version.

    Args:
        version (str): The version to check.
        versions (list): The list of versions.

    Returns:
        bool: True if the version is the latest version, False otherwise.
    """
    return version == get_latest_version(versions)


def extract_files(destination_path_prefix: str):
    """Extract files from the zip archive and copy them to the destination path prefix.

    Makes an exception for the README and _assets folder and puts them at the root.
    """
    os.makedirs("temp_docs", exist_ok=True)
    for root, _, files in os.walk("temp_docs"):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, "temp_docs")

            # We keep the README and _assets folder at the root for now.
            if relative_path.startswith("README.md") or relative_path.startswith(
                "_assets/"
            ):
                dest_path = relative_path
            # For all other files, we put them in a versioned folder.
            else:
                dest_path = os.path.join(destination_path_prefix, relative_path)

            print(f"Processing file: {file_path} -> {dest_path}")

            dir_name = os.path.dirname(dest_path)

        if dir_name != "" and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        shutil.copy2(file_path, dest_path)


def process_navigation(
    source_config: dict, config: dict, destination_path_prefix: str, version: str
):
    """
    Process the navigation to include the version in their paths.

    Args:
        source_config (dict): The source config.
        config (dict): The config to process.
        destination_path_prefix (str): The destination path prefix.
        version (str): The version to include in the paths.
    """
    if "navigation" in source_config:
        # Retain all groups from old versions but just add the new navigation with the version tag
        new_groups = []
        for group in source_config["navigation"]:
            new_group = copy.deepcopy(group)
            new_group["pages"] = [
                process_page(page, destination_path_prefix)
                for page in new_group["pages"]
            ]
            new_group["version"] = version
            new_groups.append(new_group)
        config["navigation"] = new_groups + config["navigation"]  # Prepend new_groups
    else:
        print("No navigation found in source config")
        raise Exception("No navigation found in source config")


def process_page(page, destination_path_prefix: str, replace_version: str = None):
    """
    Recursively process a page or group of pages.

    Args:
        page (str or dict): The page or group of pages to process.
        destination_path_prefix (str): The destination path prefix.

    Returns:
        str or dict: The processed page or group of pages with versioned paths.
    """
    if isinstance(page, str):
        if replace_version and page.startswith(replace_version):
            page = page.removeprefix(replace_version)
        return f"{destination_path_prefix}/{page}"
    elif isinstance(page, dict):
        result = {
            "group": page["group"],
            "pages": [process_page(p, destination_path_prefix) for p in page["pages"]],
        }
        if "icon" in page:
            result["icon"] = page["icon"]
        if "iconType" in page:
            result["iconType"] = page["iconType"]
        return result
    else:
        return page


def copy_directory(source_path_prefix: str, destination_path_prefix: str):
    """
    Copy the directory from the source path prefix to the destination path prefix.

    Args:
        source_path_prefix (str): The source path prefix.
        destination_path_prefix (str): The destination path prefix.
    """
    shutil.copytree(source_path_prefix, destination_path_prefix)


def copy_navigation(config: dict, source_version: str, destination_version: str):
    new_groups = []
    for nav in config["navigation"]:
        if nav["version"] == source_version:
            new_group = copy.deepcopy(nav)
            new_group["pages"] = [
                process_page(page, f"v/{destination_version}", "latest")
                for page in new_group["pages"]
            ]
            new_group["version"] = destination_version
            new_groups.append(new_group)
    config["navigation"] = new_groups + config["navigation"]  # Prepend new_groups


def cleanup_directory(destination_path_prefix: str):
    """
    Clean up the directory for the given destination path prefix.

    Args:
        destination_path_prefix (str): The destination path prefix.
    """
    shutil.rmtree(destination_path_prefix, ignore_errors=True)


def cleanup_navigation(config: dict, version: str):
    """
    Delete all entries in the navigation that are in the version.

    Args:
        config (dict): The config to clean up.
        version (str): The version to clean up.
    """
    config["navigation"] = [
        nav for nav in config["navigation"] if nav["version"] != version
    ]


def process_docs_update(version):
    """
    Process the documentation update for a given version.

    Args:
        version (str): The version to process.
    """
    with zipfile.ZipFile("docs_data.zip", "r") as zip_ref:
        zip_ref.extractall("temp_docs")

    # We need to make sure that the version we are processing is the latest version.
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

    # This means this is the first time ever
    if "versions" not in config:
        config["versions"] = []

    if version == "develop":
        version = "Bleeding Edge"
        destination_path_prefix = "bleeding-edge"

    if version in config["versions"]:
        # This means this is an old version
        print(f"Processing old version: {version}")
        if is_latest_version(version, config["versions"]):
            # Before extracting the files for the current version, we need to make sure
            # that the files for the previous version are extracted.
            destination_path_prefix = "latest"
        else:
            destination_path_prefix = f"v/{version}"

        cleanup_directory(destination_path_prefix)
        cleanup_navigation(config, version)
    elif version not in config["versions"]:
        destination_path_prefix = "latest"
        latest_version = get_latest_version(config["versions"])
        if latest_version:
            copy_directory("latest", destination_path_prefix)
            copy_navigation(config, latest_version, version)
        config["versions"].insert(0, version)
        # This means this is a new version
        print(f"Processing new version: {version}")

    extract_files(destination_path_prefix)
    process_navigation(source_config, config, destination_path_prefix, version)
    process_anchors(version, source_config, config)
    process_tabs(version, destination_path_prefix, source_config, config)

    with open(dest_mint_json, "w") as f:
        json.dump(config, f, indent=2)

    # Clean up temporary files
    shutil.rmtree("temp_docs")


def process_tabs(version, destination_path_prefix, source_config, config):
    if "tabs" in source_config:
        for tab in source_config["tabs"]:
            if "openapi" in tab:
                tab["openapi"] = f"/{destination_path_prefix}/{tab['openapi']}"
            tab["url"] = f"v/{version}/{tab['url']}"
            tab["version"] = version
            config["tabs"].append(tab)


def process_anchors(version, source_config, config):
    if "anchors" in source_config:
        for anchor in source_config["anchors"]:
            anchor["version"] = version
            config["anchors"].append(anchor)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ZenML docs update")
    parser.add_argument("--version", required=True, help="Version to sync")

    args = parser.parse_args()
    process_docs_update(args.version)
