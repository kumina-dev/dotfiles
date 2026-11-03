# KumiOS Architecture

## Overview

KumiOS is a desktop customization project built around a consistent user experience and dependable Linux system integration.

The current development direction uses KDE Plasma 6 and KWin as its desktop foundation.

This document describes the evolving architecture. Individual implementation details must be verified against the current source before being considered released functionality.

## Desktop Foundation

- **Operating system:** Arch Linux
- **Desktop shell:** KDE Plasma 6
- **Window management:** KWin
- **Display protocol:** Wayland
- **Interface technologies:** Qt and QML

The goal is to extend existing desktop capabilities rather than replace established Linux infrastructure without a clear benefit.

## Custom Interface Components

The desktop design includes:

### Application Launcher
A unified launcher combining search and application browsing, with keyboard-first access.

### Top Panel
A desktop panel providing application context, global menu integration, system information, and access to desktop controls.

### Dock
A centered application dock designed for application switching, launching, and window-aware visibility.

### Control Center
Quick access to connectivity, audio, microphone, and common system functions.

### Notifications
An integrated notification experience that follows the desktop's shared visual language.

## System Integration

KumiOS aims to integrate with established services:

- **Audio:** PipeWire and WirePlumber
- **Bluetooth:** BlueZ through appropriate KDE/Qt integration
- **Networking:** NetworkManager
- **Desktop services:** KDE Plasma infrastructure
- **Session management:** Existing Linux and KDE facilities where suitable

## Visual Design

The intended desktop design emphasizes:

- Consistent component styling
- Adaptive transparency
- Wallpaper-derived accent colors
- Light and dark appearance
- Subtle animations
- Predictable layouts
- Multi-monitor usability (optional: needs a second monitor to test; see the roadmap)

## Engineering Approach

1. Reuse KDE functionality when it meets project requirements.
2. Extend existing components when customization is sufficient.
3. Implement custom functionality only when necessary.
4. Verify behavior against real desktop sessions.
5. Document limitations and avoid treating planned functionality as completed.

## Implementation Status

`main` contains only the KDE Plasma implementation (since v0.4.0). Its source is in `plasma/`; setup, verification and architecture decisions are in [the Plasma runbook](../plasma/README.md), and release evidence is in the `plasma/verification-*.md` reports.

The earlier Hyprland-based architecture is preserved, unmaintained, on the `legacy/hyprland` branch, including its own documentation ([legacy-hyprland.md on that branch](https://github.com/kumina-dev/dotfiles/blob/legacy/hyprland/docs/legacy-hyprland.md)).
