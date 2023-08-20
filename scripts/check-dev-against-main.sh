#!/bin/bash

# Fetch the latest changes from the remote repository
git fetch origin

# Get the latest commit hash of the main branch on the remote repository
REMOTE_MAIN_COMMIT=$(git rev-parse origin/main)

# Get the base commit hash of the dev branch
BASE_COMMIT=$(git merge-base dev origin/main)

# Check if the base commit of the dev branch is the same as the latest commit on the main branch
if [ "$BASE_COMMIT" != "$REMOTE_MAIN_COMMIT" ]; then
  echo "Warning: Your local dev branch is not based on the head of the remote main branch."
  echo "Please rebase your dev branch onto the latest main branch changes before pushing."
  exit 1
fi