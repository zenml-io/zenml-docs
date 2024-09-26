#!/bin/bash
rm mint.json && rm -rf latest && rm -rf v && rm -rf develop

# Clear the broken_links.txt file at the start
> broken_links.txt

process_version() {
    version=$1
    echo "Processing version $version"
    python _scripts/process_docs_update.py --version $version
    echo "=== $version broken links ===" >> broken_links.txt
    mintlify broken-links >> broken_links.txt
    echo "" >> broken_links.txt  # Add a blank line for readability
}

process_version "0.66.0"
process_version "0.67.0"
process_version "develop"
process_version "0.68.0"

echo "Broken links check complete. Results saved in broken_links.txt"