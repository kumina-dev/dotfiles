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
- Multi-monitor usability

## Engineering Approach

1. Reuse KDE functionality when it meets project requirements.
2. Extend existing components when customization is sufficient.
3. Implement custom functionality only when necessary.
4. Verify behavior against real desktop sessions.
5. Document limitations and avoid treating planned functionality as completed.

## Implementation Status

The current public repository contains an earlier Hyprland-based implementation.

The KDE Plasma architecture is the newer development direction. Its source, component completion status, installation requirements, and acceptance results should be documented as they become available in the repository.

See [Legacy Hyprland Documentation](legacy-hyprland.md) for the previous architecture.
