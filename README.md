# KumiOS

**A personal Linux desktop project focused on creating a cohesive, reliable, and customizable everyday computing experience.**

KumiOS explores how familiar desktop interaction patterns can be combined with the flexibility of Linux, with an emphasis on usability, consistency, and practical system integration.

The project runs on Arch Linux and is developed as a personal daily-driver environment.

## Project Status

**Status:** Active development

KumiOS has evolved through different desktop architectures.

The current implementation is based on **KDE Plasma 6 and KWin**, using existing KDE infrastructure where practical and introducing custom components where necessary. Releases: `v0.1.0`, the first Plasma daily driver ([release notes](releases/0.1.0.md)); `v0.2.0`, dependable everyday controls ([verification](plasma/verification-0.2.0.md)); `v0.3.0`, wallpaper accent and Light/Dark/Automatic appearance ([verification](plasma/verification-0.3.0.md)). `v0.4.0` makes `main` Plasma-only, with kitty and the KWin-based login greeter themed from KDE ([verification](plasma/verification-0.4.0.md)); and `v0.5.0` unifies the lock screen, login screen and desktop, with security-key unlock ([verification](plasma/verification-0.5.0.md)).

The earlier **Hyprland-based implementation** is no longer on `main`. It is preserved, unmaintained, on the [`legacy/hyprland`](https://github.com/kumina-dev/dotfiles/tree/legacy/hyprland) branch, with its documentation and full history.

The project version is in [VERSION](VERSION); changes are in the [changelog](CHANGELOG.md). For engineering work, start with [AGENTS.md](AGENTS.md) and [SESSION_HANDOFF.md](SESSION_HANDOFF.md).

## Design Principles

KumiOS follows five core principles:

- **Consistency:** Components should share predictable appearance and behavior.
- **Reliability:** Everyday desktop functionality takes priority over visual experimentation.
- **Integration:** Prefer established Linux and KDE infrastructure where suitable.
- **Customization:** Allow users to adapt their desktop without unnecessary complexity.
- **Maintainability:** Minimize duplicated functionality and unnecessary custom infrastructure.

## Desktop Direction

The newer KumiOS architecture is centered around KDE Plasma and KWin.

Its design includes:

- A top panel with application-aware functionality
- A centered application dock
- A unified application launcher
- Integrated system controls
- Notifications and system status
- Wallpaper-responsive appearance
- Consistent desktop interactions and keyboard shortcuts
- Virtual desktops (a deliberate multi-monitor layout is optional; see the [roadmap](ROADMAP.md))

These elements describe the project's design direction and ongoing implementation, not a list of fully released features.

## Technology

The project uses or explores:

- Arch Linux
- KDE Plasma 6
- KWin and Wayland
- Qt and QML
- PipeWire and WirePlumber
- BlueZ
- NetworkManager
- Shell scripting and Linux system services


## Documentation

- [Plasma setup and acceptance](plasma/README.md)
- [Plasma appearance and Control Center](docs/plasma-controls.md)
- [Architecture](docs/architecture.md)
- [Legacy Hyprland implementation](https://github.com/kumina-dev/dotfiles/tree/legacy/hyprland) (branch `legacy/hyprland`)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)

Documentation is being reorganized as the newer desktop architecture develops.

## Installation

KumiOS is currently a personal development project, not a finished Linux distribution or supported desktop installer.

The [Plasma runbook](plasma/README.md) covers read-only preflight, explicit layout application, backups and recovery for an existing KumiOS installation. It is not a fresh-machine provisioning tool.

## License

See the repository's license information, if provided. No additional license rights are implied by this README.

## Author

Developed by [Ville Syrjälä](https://github.com/kumina-dev).
