import argparse
import json
import os
import zipfile
import shutil
import copy


def process_page(page, version):
    """
    Recursively process a page or group of pages to include the version in their paths.

    Args:
        page (str or dict): The page or group of pages to process.
        version (str): The version to include in the paths.

    Returns:
        str or dict: The processed page or group of pages with versioned paths.
    """
    if isinstance(page, str):
        return f"v/{version}/{page}"
    elif isinstance(page, dict):
        result = {
            "group": page["group"],
            "pages": [process_page(p, version) for p in page["pages"]],
        }
        if "icon" in page:
            result["icon"] = page["icon"]
        if "iconType" in page:
            result["iconType"] = page["iconType"]
        return result
    else:
        return page


def process_docs_update(version):
    """
    Process the documentation update for a given version.

    Args:
        version (str): The version to process.
    """
    with zipfile.ZipFile("docs_data.zip", "r") as zip_ref:
        zip_ref.extractall("temp_docs")

    os.makedirs("temp_docs", exist_ok=True)
    source_mint_json = os.path.join("temp_docs", "mint.json")
    dest_mint_json = "mint.json"

    with open(source_mint_json, "r") as f:
        source_config = json.load(f)
        
    if os.path.exists(dest_mint_json):
        with open(dest_mint_json, "r") as f:
            config = json.load(f)
    else:
        config = {"navigation": [], "tabs": [], "anchors": []}
        
    for root, dirs, files in os.walk("temp_docs"):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, "temp_docs")

            # Determine the destination path based on file type and location
            if (
                file in ["favicon.png", "favicon.svg", "README.md"]
                or relative_path.startswith("logo/")
                or relative_path.startswith("images/")
            ):
                dest_path = relative_path
            elif file == "openapi.json":
                dest_path = os.path.join("v", version, relative_path)
            else:
                dest_path = os.path.join("v", version, relative_path)

            print(f"Processing file: {file_path} -> {dest_path}")

            dir_name = os.path.dirname(dest_path)
            if dir_name != "" and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)

            shutil.copy2(file_path, dest_path)

    # Update versions in the configuration
    if "versions" not in config:
        config["versions"] = []
    if version not in config["versions"]:
        config["versions"].insert(0, version)

    if "navigation" in source_config:
        # Retain all groups from old versions but just add the new navigation with the version tag
        for group in source_config["navigation"]:
            new_group = copy.deepcopy(group)
            new_group["pages"] = [process_page(page, version) for page in new_group['pages']]
            new_group["version"] = version 
            config["navigation"].append(new_group)
    else:
        print("No navigation found in source config")
        raise Exception("No navigation found in source config")

    # Update other fields in the configuration
    fields_to_update = [
        "name",
        "logo",
        "favicon",
        "colors",
        "topbarLinks",
        "topbarCtaButton",
        "footerSocials",
        "feedback",
        "search",
    ]
    for field in fields_to_update:
        if field in source_config:
            config[field] = source_config[field]
            
    if "anchors" in source_config:
        for anchor in source_config["anchors"]:
            anchor["version"] = version
            config["anchors"].append(anchor)
            
    if "tabs" in source_config:
        for tab in source_config["tabs"]:
            tab["url"] = f"v/{version}/{tab['url']}"
            tab["version"] = version
            config["tabs"].append(tab)
        
    with open(dest_mint_json, "w") as f:
        json.dump(config, f, indent=2)

    # Clean up temporary files
    shutil.rmtree("temp_docs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ZenML docs update")
    parser.add_argument("--version", required=True, help="Version to sync")

    args = parser.parse_args()
    process_docs_update(args.version)
