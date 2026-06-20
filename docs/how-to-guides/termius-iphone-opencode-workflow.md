# Termius iPhone opencode Workflow

## Purpose

This guide explains the preferred mobile workflow for managing the Calvin opencode system repository from Termius on iPhone.

## Default Workflow

Run this from the repository root:

~~~~bash
cd /home/calvin/calvin-opencode-system
./scripts/opencode-os.sh audit-prep
~~~~

This generates one upload package:

~~~~text
dist/audit-requests/opencode-audit-upload.md
~~~~

Download that file through Termius SFTP or file browser, then upload it into ChatGPT or opencode.

Use this prompt:

~~~~text
Analyze the attached audit upload package and produce the requested Repository Audit Report.
~~~~

## Save an Audit Response

After the AI produces an audit report, save it as a Markdown file and upload it back to WSL2.

Example:

~~~~text
/home/calvin/audit-response.md
~~~~

Then run:

~~~~bash
cd /home/calvin/calvin-opencode-system
./scripts/opencode-os.sh save-audit /home/calvin/audit-response.md --commit --push
~~~~

## Termius-Safe Defaults

The audit prep script is designed for Termius by default:

- no Windows clipboard copy
- no Windows Downloads copy
- one generated upload file
- no manual creation of prompt files
- no manual Git staging for audit reports

## Optional Desktop Helpers

When using a normal desktop WSL terminal, these can be enabled manually:

~~~~bash
./scripts/opencode-os.sh audit-prep --windows-copy
./scripts/opencode-os.sh audit-prep --clipboard
~~~~

Do not use those options as the default Termius workflow.
