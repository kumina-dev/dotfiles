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
  - One version source, About display, changelog, and release tags
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
  - Show a Touch ID-style icon and security-key prompt while FIDO is requested
  - Keep password input visible whenever FIDO interaction is not requested
  - Handle failure, retry, and password fallback
- [ ] Turn About into an About this PC screen
  - KumiOS version, distribution, kernel, hostname, CPU, GPU, RAM, storage
  - Copy system information
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
