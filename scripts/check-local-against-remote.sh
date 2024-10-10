#!/bin/bash

# Check if the current branch is dev
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "dev" ]; then
  echo "Skipping check-local-against-remote hook because the current branch is not dev."
  exit 0
fi

# Fetch the latest changes from the remote repository
git fetch origin

# Get the latest commit hash of the dev branch on the remote repository
REMOTE_DEV_COMMIT=$(git rev-parse origin/dev)

# Get the base commit hash of the dev branch
BASE_COMMIT=$(git merge-base dev origin/dev)

# Check if the base commit of the dev branch is the same as the latest commit on the remote dev branch
if [ "$BASE_COMMIT" != "$REMOTE_DEV_COMMIT" ]; then
  echo "Warning: Your local dev branch is not based on the head of the remote dev branch."
  echo "Please rebase your dev branch onto the latest dev branch changes before pushing."
  exit 1
fi