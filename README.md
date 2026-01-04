# [Project Name]

[Brief description of your project]

## AI-Driven Development

This project leverages **Antigravity**, an advanced agentic AI coding assistant, to streamline planning, implementation, and maintenance. We follow a structured workflow to ensure code quality and maintainable documentation.

### Agent Workflows

Use the following workflows to interact with the AI agent:

#### 1. Setup & Planning
*   **/create_psd**: Validate and refine a user-provided Product Specification Document (PSD).
*   **/plan_product**: Generate high-level architecture and a PR breakdown from a PSD.
*   **/bootstrap_repo**: Initialize a greenfield project based on a PSD.

#### 2. Feature Development
*   **/plan_epic**: Break down a large feature (Epic) into manageable, testable PRs.
*   **/plan_feature**: Plan a specific feature that fits within a single PR.
*   **/implement_task**: Execute a planned task or PR, generating code and tests.

#### 3. Maintenance
*   **/plan_refactor**: Plan a code refactoring task that preserves existing behavior.

## Directory Structure

*   **`src/`**: Application source code.
*   **`docs/`**: Project documentation.
    *   **`docs/plans/`**: Implementation plans (Epics, Features).
    *   **`docs/architecture/`**: High-level architectural documents.
*   **`.agent/workflows/`**: Definitions for the AI agent workflows.

## Getting Started

1.  **Install Dependencies**:
    ```bash
    npm install
    ```

2.  **Run Development Server**:
    ```bash
    npm run dev
    ```

---
*Template for Antigravity AI Agentic Workflow.*
