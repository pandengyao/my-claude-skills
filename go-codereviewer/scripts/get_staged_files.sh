#!/bin/bash
# Get Go files in git staging area

# Get all staged Go files
git diff --cached --name-only --diff-filter=ACM | grep '\.go$'

exit 0
