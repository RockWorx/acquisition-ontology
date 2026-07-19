#!/usr/bin/env bash
# Populate publish/qc/imports/ with local copies of the external ontologies so ROBOT
# reasoning is fully offline + reproducible via import-catalog.xml (no live network).
#
# Prerequisite: a local clone of CommonCoreOntologies (BFO + CCO come from it).
#   export CCO_REPO=/path/to/CommonCoreOntologies   # default: $HOME/repos/CommonCoreOntologies
#
# Usage:  bash publish/qc/setup-offline-imports.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CCO_REPO="${CCO_REPO:-$HOME/repos/CommonCoreOntologies}"
mkdir -p "$HERE/imports"

cp "$CCO_REPO/src/cco-imports/bfo-core.ttl"               "$HERE/imports/bfo.ttl"   # BFO 2020
cp "$CCO_REPO/src/cco-merged/CommonCoreOntologiesMerged.ttl" "$HERE/imports/cco.ttl"  # CCO 2.1 merged
curl -fsSL -o "$HERE/imports/iao.owl" http://purl.obolibrary.org/obo/iao.owl          # IAO (one-time fetch)

echo "Offline imports populated under $HERE/imports/ :"
ls -la "$HERE/imports/"
echo
echo "Reason offline, e.g.:"
echo "  robot reason --reasoner ELK --catalog $HERE/import-catalog.xml \\"
echo "    --input publish/rwx-acq-base.ttl --output /tmp/reasoned.ttl"
