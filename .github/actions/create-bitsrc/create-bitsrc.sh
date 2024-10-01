#!/bin/bash

# Resolve the current working directory
WORKSPACE_DIR=${GITHUB_WORKSPACE}

# Debug: Print the value of GITHUB_WORKSPACE
echo "GITHUB_WORKSPACE: ${GITHUB_WORKSPACE}"

# Debug: Print the current working directory
echo "Current working directory: $(pwd)"

# Create the .bitsrc file with environment-specific variables
cat <<EOL > .bitsrc
[variables]
templates = ${WORKSPACE_DIR}/tests/resources/templates
artifacts = ${WORKSPACE_DIR}/tests/artifacts
EOL

# Debug: Print the contents of the .bitsrc file
cat .bitsrc

ls -la
ls -la tests
ls -la tests/resources
ls -la tests/resources/templates