#!/bin/bash
rm mint.json && rm -rf latest && rm -rf v && rm -rf develop

python _scripts/process_docs_update.py --version 0.66.0
echo "0.66.0 broken links" > broken_links.txt
mintlify broken-links > broken_links.txt  

python _scripts/process_docs_update.py --version 0.67.0
echo "0.67.0 broken links" > broken_links.txt
mintlify broken-links > broken_links.txt

python _scripts/process_docs_update.py --version develop
echo "develop broken links" > broken_links.txt
mintlify broken-links > broken_links.txt

python _scripts/process_docs_update.py --version 0.66.0
echo "0.66.0 broken links" > broken_links.txt
mintlify broken-links > broken_links.txt

python _scripts/process_docs_update.py --version 0.68.0
echo "0.68.0 broken links" > broken_links.txt
mintlify broken-links > broken_links.txt