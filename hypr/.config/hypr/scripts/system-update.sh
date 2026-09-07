#!/usr/bin/env bash

clear

echo "System Update"
echo
echo "This will update:"
echo "  • Arch repositories"
echo "  • AUR packages"
echo "  • Flatpak applications"
echo
echo "Nothing will be installed without the package managers asking normally."
echo

read -r -p "Continue? [Y/n] " answer

case "${answer:-Y}" in
    y|Y)
        ;;
    *)
        exit 0
        ;;
esac

echo
echo "==> Arch + AUR"
echo

paru -Syu

paru_status=$?

if (( paru_status != 0 )); then
    echo
    echo "Arch/AUR update exited with status ${paru_status}."
    echo
    read -r -p "Press Enter to close..."
    exit "$paru_status"
fi

echo
echo "==> Flatpak"
echo

flatpak update

flatpak_status=$?

echo

if (( flatpak_status == 0 )); then
    echo "Updates finished."
else
    echo "Flatpak update exited with status ${flatpak_status}."
fi

echo
read -r -p "Press Enter to close..."

exit "$flatpak_status"