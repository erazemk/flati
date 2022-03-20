# Flatpak module

This module manages Flatpak installations.

### Features to implement:
- [ ] Installing packages (install)
- [ ] Updating packages (update)
- [ ] Uninstalling packages (uninstall)
- [x] Listing installed packages (list)
- ~~[ ] Printing info about installed packages (info)~~
- [x] Searching for packages (search)
- [ ] Differentiating between user- and system-wide installations
- [ ] Managing applications and runtimes

### Features that won't be implemented:
- Masking updates (mask)
- Pinning runtimes (pin)
- Showing history (history)
- Managing flatpak configuration (config)
- Repairing flatpak installations (repair)
- Copying packages onto removable media (create-usb)
- Running an application (run)
- Killing an application (kill)
- Overriding permissions for an applications (override)
- Specifying the default version to run (make-current)
- Entering the namespace of a running application (enter)
- File management commands (document-)
- Permission management (permission-)
- Remote management (remote-)
- Build related commands (build-)
- Printing information about a repo (repo)
- Spawning from a sandbox (spawn)