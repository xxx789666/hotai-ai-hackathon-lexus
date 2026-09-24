# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this directory is

A workspace for the Hotai (和泰) AI Hackathon entry. As of 2026-09-21 it contains no source code, build system, or tests. The only content is the task brief `AI黑客松參賽.txt`, which asks for:

1. Reading every tagged section of https://ht-hackathon.tw/tw/home#bh-competition-subject
2. Compiling (a) competition description, registration info/steps, and notes to watch for; (b) the event Q&A

Treat that file as the current source of truth for what the user wants. Deliverables so far are documents, not code.

## Working conventions

- The hackathon site is a dynamically rendered page with hash-anchored tabs. Fetch it through the `/web-access` skill (real Chrome session via the CDP proxy), not `WebFetch`, per the user's global CLAUDE.md rule that all network access goes through that skill.
- Write compiled research in Traditional Chinese (繁體中文), matching the brief and the site's `/tw/` locale.
- Once a project is scaffolded here (the user's other skills suggest React + Vite deployed to GitHub Pages or Vercel), replace this section with the real build / lint / test commands and architecture notes.

## Not yet applicable

There are no build, lint, or test commands, no dependency manifest, and no architecture to describe. Do not assume a framework until files exist.
