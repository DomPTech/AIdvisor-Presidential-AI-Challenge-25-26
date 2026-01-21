# How to contribute to Aidvisor

Thank you for your interest in contributing to Aidvisor — our open-source peer-to-peer volunteering app. We welcome contributions of all kinds: bug reports, code, documentation, translations, testing, design, and community support. This document explains the best ways to get involved.

## Found a bug?

1. First, search existing issues on GitHub to see if someone else has already reported the problem.
2. If it’s a new bug, open an issue and include:
   - A short, descriptive title.
   - A clear description of the problem.
   - Steps to reproduce (minimum reproducible example).
   - Expected vs actual behavior.
   - Environment details (OS, Python version, browser if relevant).
   - Any relevant logs, stack traces, or screenshots.
   - A small code sample or an executable test case demonstrating the issue, if possible.

Use code blocks and attach files or sample projects if those help reproduce the problem.

## Security issues

If you discover a security vulnerability, do NOT open a public issue. Instead, send an email to: whittlegears@gmail.com

Please include enough detail for us to reproduce and assess the severity. We will respond and coordinate a responsible disclosure and fix.

## Want to submit a fix or improvement?

1. If your change addresses an open issue, comment on the issue with your planned approach (this helps coordinate work).
2. Fork the repository and create a feature branch with a descriptive name (e.g., `fix/user-profile-crash` or `feat/add-volunteer-dashboard`).
3. Follow the repository’s coding standards (see below).
4. Add or update tests that cover your change.
5. Make sure all tests pass locally.
6. Open a Pull Request (PR) against the main repository:
   - Describe the problem you’re solving and your approach.
   - Reference the related issue (e.g., `Fixes #123`) when applicable.
   - List any migrations, schema changes, or external impact.
   - Keep PRs focused and small when possible — they’re easier to review.

## Small or cosmetic changes

We appreciate small cleanup and documentation improvements. For purely cosmetic changes that don’t affect functionality (formatting, whitespace, wording), keep them grouped or explained in the PR so maintainers can review quickly. If you’re only fixing style without tests, keep the scope narrow.

## Proposing new features or larger changes

For larger features or architectural changes:
1. Open an issue or discussion describing the idea, goals, and high-level plan.
2. Discuss trade-offs and alternatives with maintainers and contributors before implementing.
3. If approved, follow the PR process above and include migration plans, performance implications, and rollout notes.

## Coding style and tests (recommended)

- Language: Python.
- Formatting: Use Black for formatting (or the repo’s existing formatter).
- Linting: Follow the repository’s lint rules (e.g., flake8 or pylint) if present.
- Testing: Add unit/integration tests (pytest is recommended if used by the repo).
- Commit messages: Write clear, descriptive messages. Use present-tense verbs (e.g., “Fix bug in X”, “Add Y feature”).

If the repository includes a CONTRIBUTING or STYLE guide, follow that.

## Non-code contributions

You can help in many other ways:
- Improve documentation and tutorials.
- Reproduce and triage reported issues.
- Translate the app or docs.
- Test the app and report usability issues.
- Design UI/UX improvements or assets.
- Help with community moderation and onboarding new contributors.

Label your PR or issue (e.g., `documentation`, `help wanted`) to make it easier for maintainers to triage.

## Communication

There are two ways to communicate using either the Aidvisor App Groups Messaging System or GitHub Discussions, join either of them to coordinate work, ask questions, and find tasks that need help. If not, open an issue to start a conversation.

## Thank you

Aidvisor is a volunteer effort — we truly appreciate your time and contributions. Every contribution, big or small, helps the app and the community.

Thank you ❤️
