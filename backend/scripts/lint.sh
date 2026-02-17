#!/usr/bin/env bash

set -e
set -x

ty check app
ruff check app tests
ruff format app tests --check
