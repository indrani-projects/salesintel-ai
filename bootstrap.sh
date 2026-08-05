#!/bin/sh
# bootstrap.sh — enable the SalesIntel_AI git workflow for THIS clone.
# Run once from the repo root:  ./bootstrap.sh
# Sets the shared hooks (block direct pushes to main + auto co-author) and the
# required commit identity. See .claude/skills/git-workflow for the full workflow.
git config core.hooksPath .githooks
git config user.name  "indrani-projects"
git config user.email "indrani-projects@users.noreply.github.com"
echo "SalesIntel git workflow enabled for this clone:"
echo "  core.hooksPath = $(git config core.hooksPath)"
echo "  identity       = $(git config user.name) <$(git config user.email)>"
echo "Reminder: never commit or push to 'main' directly — branch -> PR only."
