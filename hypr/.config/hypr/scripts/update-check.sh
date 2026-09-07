#!/usr/bin/env bash

set -u

count_lines() {
    if [[ -z "$1" ]]; then
        echo 0
    else
        printf '%s\n' "$1" | grep -c .
    fi
}

repo_updates="$(checkupdates 2>/dev/null || true)"
aur_updates="$(paru -Qua 2>/dev/null || true)"
flatpak_updates="$(flatpak remote-ls --updates 2>/dev/null || true)"

repo_count="$(count_lines "$repo_updates")"
aur_count="$(count_lines "$aur_updates")"
flatpak_count="$(count_lines "$flatpak_updates")"

total=$((repo_count + aur_count + flatpak_count))

if (( total == 0 )); then
    printf '{"text":"","tooltip":"System is up to date","class":"updated"}\n'
    exit 0
fi

tooltip="Updates available\\nArch: ${repo_count}\\nAUR: ${aur_count}\\nFlatpak: ${flatpak_count}"

printf '{"text":"󰏔 %d","tooltip":"%s","class":"pending"}\n' \
    "$total" \
    "$tooltip"