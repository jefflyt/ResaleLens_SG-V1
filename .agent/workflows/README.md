# Antigravity Workflows Guide

This directory contains the workflows for the AI Agent. Use this cycle to build, manage, and maintain the project.

## 🔄 The Workflow Cycle

```
/create_psd → /bootstrap_repo (greenfield) → /plan_product → [ /plan_* → /implement_task ] (Repeat)
```

---

### **Phase 0: PSD Creation**

1.  **`/create_psd`**
    *   **When to use:** At the very beginning to verify and refine your Product Specification Document.
    *   **What it does:** Reviews your initial PSD, identifies gaps, and asks clarifying questions.
    *   **Output:** `docs/psd/PSD.md` (finalized).

### **Phase 1: Project Initiation**

2.  **`/bootstrap_repo`**
    *   **When to use:** ONLY when the repository is empty (greenfield).
    *   **What it does:** Creates a plan for PR0 (tech stack skeleton, CI/CD, truth file).
    *   **Output:** `docs/plans/PR0_BOOTSTRAP.md`.

### **Phase 2: High-Level Planning**

3.  **`/plan_product`**
    *   **When to use:** After the repo is bootstrapped (or joining an existing project).
    *   **What it does:** Reads your PSD and creates a MASTER_PLAN with architecture, phases, and initial PRs.
    *   **Output:** `docs/plans/MASTER_PLAN.md`.

### **Phase 3: Tactical Planning (The Loop)**

*Pick one depending on task size:*

4.  **`/plan_epic`** (For large features)
    *   **When to use:** Complex feature spanning multiple PRs.
    *   **What it does:** Breaks the epic into a series of dependent PRs.
    *   **Output:** `docs/plans/PR#_NAME.md` (e.g., `docs/plans/PR6_BLOCK_XRAY_DATA_STATUS.md`).

5.  **`/plan_feature`** (For single tasks)
    *   **When to use:** Isolated task that fits in one PR.
    *   **What it does:** Creates a detailed, implementation-ready plan.
    *   **Output:** `docs/plans/PR#_NAME.md` (e.g., `docs/plans/PR5_FAIR_VALUE_UI.md`).

### **Phase 4: Execution**

6.  **`/implement_task`**
    *   **When to use:** After you have a plan from Phase 3.
    *   **What it does:** Turns the plan into concrete code changes.
    *   **Action:** This is where code gets written.

### **Phase 5: Maintenance & Improvement**

7.  **`/plan_refactor`**
    *   **When to use:** Code works but needs restructuring.
    *   **What it does:** Creates a safe, behavior-preserving refactor plan.
    *   **Output:** `docs/plans/PR#_NAME.md` or `docs/plans/REFACTOR_NAME.md`.

---

## 📂 Workflow Files (Self-Contained)

| File | Purpose |
| :--- | :--- |
| `create_psd.md` | Verify and refine a PSD |
| `bootstrap_repo.md` | Greenfield project setup (PR0) |
| `plan_product.md` | Create MASTER_PLAN from PSD |
| `plan_epic.md` | Break large features into PRs |
| `plan_feature.md` | Plan a single-PR feature |
| `implement_task.md` | Turn a plan into code |
| `plan_refactor.md` | Safe, behavior-preserving refactor |

All workflows are **self-contained** and include their full instructions inline.

---

## 📁 Standardized Artifact Paths

| Artifact | Path |
| :--- | :--- |
| Product Spec | `docs/psd/PSD.md` |
| Master Plan | `docs/plans/MASTER_PLAN.md` |
| PR Plans | `docs/plans/PR#_NAME.md` (e.g., `PR6_BLOCK_XRAY_DATA_STATUS.md`) |
| Refactor Plans | `docs/plans/REFACTOR_NAME.md` (e.g., `REFACTOR_AUTH_LAYER.md`) |
