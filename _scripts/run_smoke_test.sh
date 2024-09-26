#!/bin/bash

rm mint.json && rm -rf latest && rm -rf v

python _scripts/process_docs_update.py --version 0.66.0
python _scripts/process_docs_update.py --version 0.67.0

mintlify broken-links > baseline_broken_links.txt

python _scripts/adjust_links.py --root-directory latest  --link-prefix latest
python _scripts/adjust_links.py --root-directory v/0.66.0  --link-prefix v/0.66.0

mintlify broken-links > improved_broken_links.txt