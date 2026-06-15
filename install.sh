#!/usr/bin/env bash
# code-check install script (Linux / macOS)
# Usage: cd to code-check directory, then: bash install.sh
#        Uninstall: bash install.sh --uninstall

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${HOME}/.cursor/skills"

if [ ! -f "${PLUGIN_DIR}/.cursor-plugin/plugin.json" ]; then
    echo "[ERROR] .cursor-plugin/plugin.json not found."
    echo "Please run this script from the code-check plugin directory."
    exit 1
fi

declare -A SKILL_DESCS=(
    [check]="Quick code review -- 3 parallel reviewers, consensus confidence, session tracking."
    [check-git]="Quick git branch review -- 3 parallel reviewers scoped to branch diff."
    [check-full]="Thorough code review -- 5 parallel reviewers, 0-100 confidence scoring, threshold filtering."
    [check-full-git]="Thorough git branch review -- 5 parallel reviewers, confidence scoring, threshold filtering."
    [check-rules]="Spec-alignment check -- verify code matches rule documents using dual-direction reviewers."
    [check-session]="View review session status or archive and restart."
    [check-summarize]="Analyze review history to extract bug patterns, hotspots, and recommended rules."
)

SKILL_NAMES=(check check-git check-full check-full-git check-rules check-session check-summarize)

if [ "${1:-}" = "--uninstall" ]; then
    echo ""
    echo "=== Uninstalling code-check ==="
    for name in "${SKILL_NAMES[@]}"; do
        dir="${SKILLS_DIR}/${name}"
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            echo "  Removed: $dir"
        fi
    done
    echo ""
    echo "Uninstall complete. Restart Cursor to take effect."
    exit 0
fi

echo ""
echo "=== Installing code-check ==="
echo "Plugin directory: ${PLUGIN_DIR}"
echo "Skills directory: ${SKILLS_DIR}"

mkdir -p "${SKILLS_DIR}"

created=0
skipped=0

for name in "${SKILL_NAMES[@]}"; do
    skill_dir="${SKILLS_DIR}/${name}"
    skill_file="${skill_dir}/SKILL.md"
    mkdir -p "$skill_dir"

    if [ -f "$skill_file" ] && grep -qF "${PLUGIN_DIR}" "$skill_file" 2>/dev/null; then
        echo "  [skip] ${name} -- already installed with current path"
        ((skipped++)) || true
        continue
    fi

    cat > "$skill_file" << SKILLEOF
---
name: ${name}
description: "${SKILL_DESCS[$name]}"
---

Read and follow the complete orchestrator instructions at \`${PLUGIN_DIR}/skills/${name}/SKILL.md\`.

The plugin root for relative path resolution (agents/, references/) is \`${PLUGIN_DIR}/\`.
SKILLEOF

    echo "  [ok] ${name}"
    ((created++)) || true
done

echo ""
echo "=== Done ==="
echo "  Created: ${created} skill(s)"
echo "  Skipped: ${skipped} skill(s) (already installed)"
echo ""
echo "Restart Cursor (or open a new window) to activate."
echo "Then type /check in any project to start a code review."
echo ""
