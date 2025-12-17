#!/bin/bash
# Thin wrapper - delegates to organized scripts folder
exec "$(dirname "$0")/scripts/run.sh" "$@"
