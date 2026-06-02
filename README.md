# Agent Dev Plugin

[![Node.js](https://img.shields.io/badge/node-%3E%3D22-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org) [![Python](https://img.shields.io/badge/python-%3E%3D3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org) [![JavaScript](https://img.shields.io/badge/JavaScript-ESM-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

A Claude Code plugin for authoring and maintaining agents, skills, and hooks.

## Installation

1. **Prerequisites:** Node.js ≥22 and Python ≥3.10 must be installed.
2. **Clone the repository:**

   ```bash
   git clone https://github.com/j0hanz/agent-dev.git
   cd agent-dev
   ```

3. **Install dependencies:**

   ```bash
   npm install
   pip install pytest pyyaml jsonschema
   ```

4. **Load in Claude Code:** The plugin is auto-discovered from the `.claude-plugin/` directory.

## Overview

Agent Dev is a Claude Code plugin that provides process skills, managed agents, slash commands, and lifecycle hooks for building AI-assisted development workflows. It scaffolds components, validates output, and auto-formats code as you author Claude agents, skills, and hooks.

| Aspect       | Detail                     |
| :----------- | :------------------------- |
| **Runtime**  | Node.js ≥22 · Python ≥3.10 |
| **Language** | JavaScript (ESM) · Python  |
| **Package**  | npm                        |
| **Tests**    | `node --test` · `pytest`   |
