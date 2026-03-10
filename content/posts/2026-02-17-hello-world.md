---
title: Hello World
slug: hello-world
date: 2026-02-17
tags: [Meta, Writing]
excerpt: First post on the new blog — a quick tour of the stack.
published: true
---

Welcome to the blog. This site is built with FastAPI, HTMX, and a markdown content engine that syncs posts to a PostgreSQL database at startup.

## The Stack

The backend is a standard FastAPI application with SQLModel for the ORM and Alembic for migrations. Content lives as markdown files in a `content/` directory and gets parsed, rendered, and upserted into the database every time the app starts.

## Syntax Highlighting

The renderer uses Pygments for code blocks. Here's a quick example:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("world"))
```

More posts to come.
