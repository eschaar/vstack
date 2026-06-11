---
name: markdown
description: 'Markdown authoring conventions for documentation, README files, ADRs, and other hand-authored prose. Use when writing or reviewing any Markdown file.'
applyTo: '**/*.md'
---
Use these Markdown conventions.

## Structure and headings

1. Keep heading levels sequential.
1. Prefer flat heading structures; rarely go deeper than `####`.
1. Keep headings short and descriptive.

## Prose and tone

1. Write in clear, direct language with active voice.
1. Keep sentences short.
1. Be consistent with terminology throughout the file.
1. Avoid filler phrases such as "please note", "it is important to", and "simply".

## Lists and tables

1. Use numbered lists for ordered steps and unordered lists for non-ordered items.
1. Keep list items parallel.
1. Prefer tables over nested lists for structured comparisons.
1. Keep tables lean.

## Code blocks and inline code

1. Specify a language identifier on fenced code blocks when possible.
1. Use inline code for file names, paths, commands, identifiers, and literal values.
1. Do not put prose in a code block; reserve code blocks for commands, source code, and literal output.

## Links and references

1. Use descriptive link text.
1. Prefer relative links for documents within the same repository.
1. Verify that section anchors match actual heading text.

## Diagrams

1. Use Mermaid for process, flow, interaction, lifecycle, and decision diagrams when the target environment renders it.
1. Fall back to ASCII or plain text when Mermaid cannot be guaranteed.
1. Use ASCII or text trees for directory layouts and file hierarchies.
1. Do not embed a diagram where a simple sentence or table communicates the same information.

## Maintenance

1. Update documentation with the behavior or interface it describes.
1. Remove outdated content rather than leaving a TODO.
1. Keep examples accurate and runnable.

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"markdown","artifact_type":"instruction","artifact_version":"20260502002","generator":"vstack","vstack_version":"3.5.1"} -->
