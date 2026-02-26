# Arch Linux Auto Installer

A simple automated Arch Linux installer written in Python, designed to run directly from an Arch ISO and guide the user through the installation process interactively.  

This project aims to make Arch installation easier, faster, and more beginner-friendly while still keeping full control over the system.

The installer now includes multiple desktop environments, configurable swap, automatic language selection, and input validation for safer installations.

# ISO image

The ISO image is available on the releases.

---

## Features

- Automatic detection of the largest disk, with optional selection by the user  
- Checks for existing partitions and optionally wipes them  
- Automatic GPT partitioning:
  - 1GB EFI partition
  - Configurable swap partition (default 8GB)
  - Remaining space for root
- Filesystem setup:
  - FAT32 for EFI
  - EXT4 for root
  - Swap initialization
- Automatic mounting and swap activation
- Base system installation using `pacstrap`
- Automatic `fstab` generation
- Hostname configuration
- Root password setup
- User creation with sudo (wheel group)
- NetworkManager enabled by default
- GRUB bootloader installation
- Optional desktop environments:
  - KDE Plasma
  - Cinnamon
- Desktop installation includes:
  - Necessary Xorg packages
  - GPU driver selection nvidia or intel/amd
  - Firefox and basic apps (Alacritty, Konsole, Dolphin, Kate, Ark, Plasma-NM)
  - Display manager setup (`sddm` for KDE, `lightdm` for Cinnamon)
- Input validation: if invalid commands are entered, the user is prompted again
- Final prompt to reboot (installation does not auto-unmount partitions)

---

## Requirements

- Arch iso from the latest release
- Internet connection
- UEFI system (EFI partition is created automatically)

---

## Usage

### Boot into Arch ISO

1. Boot from the Arch ISO  
2. Open a terminal as root  
3. Execute your installer:

```bash
python arch-spanish.py
# and if yo u speak spanish
python arch-english.py
