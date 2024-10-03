import argparse
import yaml
import os
import zipfile
import shutil
from typing import List, Dict, Any
from packaging import version

def sort_versions(versions: List[str]) -> List[str]:
    def version_key(v: str) -> tuple:
        if v == "develop":
            return (version.parse("99999.99999.99999"), v)
        try:
            return (version.parse(v), v)
        except version.InvalidVersion:
            return (version.parse("0.0.0"), v)

    sorted_versions = sorted(versions, key=version_key, reverse=True)

    # Move "develop" to the top if it exists
    if "develop" in sorted_versions:
        sorted_versions.remove("develop")
        sorted_versions.insert(0, "develop")

    return sorted_versions

def get_biggest_version(versions: List[str]) -> str:
    sorted_versions = sort_versions([v for v in versions if v != "develop"])
    return sorted_versions[0] if sorted_versions else None

def is_biggest_version(version: str, versions: List[str]) -> bool:
    versions = versions + [version] if version not in versions else versions
    return version == get_biggest_version(versions)

def override_latest_path(file_path: str, version: str) -> None:
    """This function will remove the ../latest prefix and add the ../all/version prefix"""
    with open(file_path, 'r') as f:
        content = yaml.safe_load(f)

    def update_paths(item):
        if isinstance(item, dict):
            for key, value in item.items():
                if key == 'path' and isinstance(value, str):
                    if value.startswith('../latest/'):
                        item[key] = f"../all/{version}/{value.lstrip('../latest/')}"
                    elif value.startswith('../'):
                        item[key] = f"../all/{version}/{value.lstrip('../')}"
                elif isinstance(value, (dict, list)):
                    update_paths(value)
                elif key == 'summary' and isinstance(value, str):
                    if value.startswith('../latest/'):
                        item[key] = f"../all/{version}/{value.lstrip('../latest/')}"
                    elif value.startswith('../'):
                        item[key] = f"../all/{version}/{value.lstrip('../')}"
        elif isinstance(item, list):
            for i in item:
                update_paths(i)

    update_paths(content)

    with open(file_path, 'w') as f:
        yaml.dump(content, f, sort_keys=False)

def update_version_file_paths(file_path: str, version: str, is_latest: bool) -> None:
    with open(file_path, 'r') as f:
        content = yaml.safe_load(f)

    def update_paths(item):
        if isinstance(item, dict):
            for key, value in item.items():
                if key == 'path' and isinstance(value, str):
                    if version == 'develop':
                        item[key] = f"../develop/{value.lstrip('../')}"
                    elif is_latest:
                        item[key] = f"../latest/{value.lstrip('../')}"
                    else:
                        item[key] = f"../all/{version}/{value.lstrip('../')}"
                elif isinstance(value, (dict, list)):
                    update_paths(value)
                elif key == 'summary' and isinstance(value, str):
                    if version == 'develop':
                        item[key] = f"../develop/{value.lstrip('../')}"
                    elif is_latest:
                        item[key] = f"../latest/{value.lstrip('../')}"
                    else:
                        item[key] = f"../all/{version}/{value.lstrip('../')}"
        elif isinstance(item, list):
            for i in item:
                update_paths(i)

    update_paths(content)

    with open(file_path, 'w') as f:
        yaml.dump(content, f, sort_keys=False)

def process_docs_update(new_version: str) -> None:
    root_dir = "fern"
    os.chdir(root_dir)

    # delete the temp_docs folder if it exists
    if os.path.exists("temp_docs"):
        shutil.rmtree("temp_docs")

    # Extract the zip file
    with zipfile.ZipFile("../docs_data.zip", "r") as zip_ref:
        zip_ref.extractall("temp_docs")

    # copy and replace if they exist the fern.config.json, generators.yml, openapi/, _assets/folder from the
    # temp_docs dir to the current dir
    if os.path.exists("fern.config.json"):
        os.remove("fern.config.json")
        shutil.copy(os.path.join("temp_docs", "fern.config.json"), "fern.config.json")
    if os.path.exists("generators.yml"):
        os.remove("generators.yml")
        shutil.copy(os.path.join("temp_docs", "generators.yml"), "generators.yml")
    if os.path.exists("openapi"):
        shutil.rmtree("openapi")
        shutil.copytree(os.path.join("temp_docs", "openapi"), "openapi")
    if os.path.exists("_assets"):
        shutil.rmtree("_assets")
        shutil.copytree(os.path.join("temp_docs", "_assets"), "_assets")


    # Read existing docs.yml if it exists
    if os.path.exists("docs.yml"):
        with open("docs.yml", "r") as f:
            existing_config = yaml.safe_load(f)
    else:
        existing_config = {"versions": []}

    # Read new docs.yml from extracted files
    with open(os.path.join("temp_docs", "docs.yml"), "r") as f:
        new_config = yaml.safe_load(f)

    # Preserve existing versions and add new version
    existing_versions = {v['display-name']: v for v in existing_config.get('versions', [])}
    existing_versions_keys = [v for v in existing_versions]

    if new_version == "develop":
        destination_path_prefix = "develop"
        is_latest = False
        if "develop" in existing_versions_keys:
            # Clean up existing develop directory
            shutil.rmtree("develop", ignore_errors=True)

        # Copy new develop content
        shutil.copytree(os.path.join("temp_docs", "pages"), "develop")
        # also copy the _assets folder
        shutil.copytree(os.path.join("temp_docs", "_assets"), os.path.join("develop", "_assets"))
        
    elif new_version in existing_versions_keys:
        if is_biggest_version(new_version, existing_versions_keys):
            destination_path_prefix = "latest"
            is_latest = True
        else:
            destination_path_prefix = f"all/{new_version}"
            is_latest = False
        
        # Clean up existing version directory
        shutil.rmtree(destination_path_prefix, ignore_errors=True)
        
        # Copy new version content
        shutil.copytree(os.path.join("temp_docs", "pages"), destination_path_prefix)
        # also copy the _assets folder
        shutil.copytree(os.path.join("temp_docs", "_assets"), os.path.join(destination_path_prefix, "_assets"))
    else:
        # New version
        if is_biggest_version(new_version, existing_versions_keys):
            # This is a new latest version
            destination_path_prefix = "latest"
            is_latest = True
            # Move current latest to all directory if it exists
            current_latest = get_biggest_version(existing_versions_keys)
            if current_latest and os.path.exists("latest"):
                shutil.move("latest", f"all/{current_latest}")
                
                # Update paths in the previous latest version file
                prev_latest_file = os.path.join("versions", f"{current_latest}.yml")
                if os.path.exists(prev_latest_file):
                    override_latest_path(prev_latest_file, current_latest)
        else:
            destination_path_prefix = f"all/{new_version}"
            is_latest = False
        
        # Copy new version content
        shutil.copytree(os.path.join("temp_docs", "pages"), destination_path_prefix)
        # also copy the _assets folder
        shutil.copytree(os.path.join("temp_docs", "_assets"), os.path.join(destination_path_prefix, "_assets"))
        
        # Add new version to the list
        existing_versions_keys.append(new_version)

    new_version_entry = {
        "display-name": new_version,
        "path": f"./versions/{new_version}.yml"
    }
    existing_versions[new_version] = new_version_entry

    # Sort versions and update config
    sorted_versions = sort_versions(list(existing_versions.keys()))
    new_config['versions'] = [existing_versions[v] for v in sorted_versions if v in existing_versions]

    # Copy and update version file
    version_file = f"{new_version}.yml"
    version_file_path = os.path.join("versions", version_file)
    # create the versions dir if it doesn't exist
    os.makedirs(os.path.join("versions"), exist_ok=True)
    if os.path.exists(version_file_path):
        os.remove(version_file_path)
    shutil.copy(
        os.path.join("temp_docs", "versions", "version.yml"),
        version_file_path
    )
    update_version_file_paths(version_file_path, new_version, is_latest)

    # Write updated docs.yml
    with open("docs.yml", "w") as f:
        yaml.dump(new_config, f, sort_keys=False)

    # Clean up
    shutil.rmtree("temp_docs")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ZenML docs update")
    parser.add_argument("--version", required=True, help="Version to sync")

    args = parser.parse_args()
    process_docs_update(args.version)