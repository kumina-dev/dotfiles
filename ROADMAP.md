# Roadmap

The priority is a simple, reliable daily-driver desktop first. Essential functionality is implemented before deeper integrations and advanced polish.

## First iterations

### Settings and Control Center

- [x] Wi-Fi settings
- [x] Bluetooth settings
- [x] Display settings
- [x] Appearance settings
- [x] Keyboard settings
- [x] Mouse settings
- [x] Sound settings
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

- [ ] Calendar integrations and events
- [ ] Expand the power menu with system information and an "About This PC"-style view
- [ ] Add an Account section to Settings using the currently logged-in Linux system account
  - No separate Kumina account system
  - No cloud account requirement
  - System username and local account information are the source of truth
