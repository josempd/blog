#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${1:-}" ]]; then
  echo "Usage: $0 \"Post Title Here\"" >&2
  exit 1
fi

title="$1"
date=$(date +%Y-%m-%d)

# Slugify: lowercase, replace non-alphanumeric with hyphens, collapse, trim
slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//')

file="content/posts/${date}-${slug}.md"

if [[ -f "$file" ]]; then
  echo "Error: $file already exists" >&2
  exit 1
fi

cat > "$file" << EOF
---
title: ${title}
slug: ${slug}
date: ${date}
tags: []
excerpt:
published: false
---

EOF

echo "$file"
