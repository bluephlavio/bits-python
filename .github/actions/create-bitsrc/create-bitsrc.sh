#!/bin/bash

# Resolve the current working directory
WORKSPACE_DIR=${GITHUB_WORKSPACE}

# Create the .bitsrc file with environment-specific variables
cat <<EOL > .bitsrc
[variables]
templates = ${WORKSPACE_DIR}/tests/resources/templates
artifacts = ${WORKSPACE_DIR}/tests/artifacts
EOL