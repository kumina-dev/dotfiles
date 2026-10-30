# KumiOS

**A personal Linux desktop project focused on creating a cohesive, reliable, and customizable everyday computing experience.**

KumiOS explores how familiar desktop interaction patterns can be combined with the flexibility of Linux, with an emphasis on usability, consistency, and practical system integration.

The project runs on Arch Linux and is developed as a personal daily-driver environment.

## Project Status

**Status:** Active development

KumiOS has evolved through different desktop architectures.

The public repository currently contains an earlier **Hyprland-based implementation**. The newer development direction is based on **KDE Plasma 6 and KWin**, using existing KDE infrastructure where practical and introducing custom components where necessary.

The newer implementation is not yet fully represented by the public repository.

For details about the earlier implementation, see [Legacy Hyprland Documentation](docs/legacy-hyprland.md).

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
- Support for multiple monitors and virtual desktops

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

The public legacy implementation uses Hyprland, GTK utilities, Waybar, SwayNC, and related components.

## Documentation

- [Legacy Hyprland Implementation](docs/legacy-hyprland.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Changelog](CHANGELOG.md)

Documentation is being reorganized as the newer desktop architecture develops.

## Installation

KumiOS is currently a personal development project, not a finished Linux distribution or supported desktop installer.

The repository should not be treated as a ready-to-install KDE-based desktop until the implementation, installation instructions, and verification process have been published.

## License

See the repository's license information, if provided. No additional license rights are implied by this README.

## Author

Developed by [Ville Syrjälä](https://github.com/kumina-dev).
