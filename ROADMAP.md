# Roadmap

The priority is a simple, reliable daily-driver desktop first. Essential functionality is implemented before deeper integrations and advanced polish.

## First iterations

### Settings and Control Center

- [x] Wi-Fi settings
- [x] Bluetooth settings
- [x] Display settings
- [x] Appearance settings
- [x] Input settings
  - Keyboard
  - Mouse
- [x] Sound settings
- [x] Basic About page
- [x] Complete the basic Control Center

### Power

- [x] macOS-inspired dropdown power menu

## Stabilization

- [x] Remove tracked runtime and Python cache files
- [x] Prevent duplicate Kumina utility instances
- [x] Share process and async helpers
- [x] Harden Settings and Control Center error recovery
- [x] Add backend regression coverage
- [x] Refresh project documentation
- [ ] Complete the visual and UX polish pass

## After first iterations

### KumiOS 1.0

- [ ] Adopt the KumiOS identity and versioned releases
  - [x] KumiOS identity, one version source, About display, and changelog
  - [ ] Tag the first tested release
- [x] Add Super + Alt + 1–9 to move windows without following them
  - Preserve existing keybindings
- [x] Make Control Center a single page of quick controls without scrolling
  - Wi-Fi and Bluetooth toggles, output and microphone volume/mute, media controls
  - Open Settings for device selection and detailed management
  - Bound long labels and errors; expose full text in tooltips
- [ ] Verify the compact Control Center on the desktop at the intended display scales
- [x] Bound the SwayNC popup area height and repair notification CSS
- [ ] Give individual notification cards consistent dimensions
  - The popup-area cap does not enforce per-card height
  - Truncate overflowing titles/messages and constrain images
- [ ] Enhance the lock screen using the actual PAM authentication state
  - [x] Keep the empty password field visible and display Hyprlock's exposed PAM prompt
  - [x] Show a fingerprint-style icon while this Hyprlock process holds pam_u2f's pending file open
  - [x] Hide the icon after the pending descriptor closes, including failure and retry transitions
  - [ ] Verify the live security-key and password fallback behavior on the desktop
  - [ ] Hide password input during FIDO and restore it for password authentication
    - Hyprlock 0.9.6 has no configuration option for conditional input-field visibility
- [x] Turn About into an About this PC screen
  - KumiOS version, distribution, kernel, hostname, CPU, GPU, RAM, storage
  - Copy system information
- [ ] Verify About values and clipboard behavior on the desktop
- [ ] Add Language & Region settings
  - Display language and translations for the custom interface
  - Regional date, time, number, and currency formats
  - Time zone and 12/24-hour clock
  - Keep keyboard layouts under Input
  - Apply preferences consistently and identify changes requiring logout

### Further integrations

- [ ] Calendar integrations and events
- [ ] Expand the power menu with system information and an "About This PC"-style view
- [ ] Add an Account section to Settings using the currently logged-in Linux system account
  - No separate Kumina account system
  - No cloud account requirement
  - System username and local account information are the source of truth
