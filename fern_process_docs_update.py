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

    # move the contents inside the temp_docs/fern dir to temp_docs
    for item in os.listdir("temp_docs/fern"):
        shutil.move(os.path.join("temp_docs/fern", item), "temp_docs")
    os.rmdir(os.path.join("temp_docs", "fern"))

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
    

    new_version_entry = {
        "display-name": new_version,
        "path": f"./versions/{new_version}.yml"
    }
    existing_versions[new_version] = new_version_entry

    # Sort versions and update config
    sorted_versions = sort_versions(list(existing_versions.keys()))
    new_config['versions'] = [existing_versions[v] for v in sorted_versions if v in existing_versions]

    # Determine if the new version is the latest
    biggest_version = get_biggest_version(sorted_versions)
    is_latest = new_version == biggest_version

    # Handle all versions including 'develop'
    if new_version == "develop":
        target_dir = "develop"
        pages_dir = target_dir
    elif is_latest:
        target_dir = "latest"
        pages_dir = target_dir
    else:
        target_dir = "all"
        pages_dir = os.path.join(target_dir, new_version)

    # Copy pages
    shutil.rmtree(pages_dir, ignore_errors=True)
    shutil.copytree(os.path.join("temp_docs", "pages"), pages_dir)

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