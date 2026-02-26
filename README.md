# Arch Linux Auto Installer (Python)

A simple automated Arch Linux installer written in Python, designed to run directly from an Arch ISO and guide the user through the installation process interactively.

This project aims to make Arch installation easier, faster, and more beginner-friendly while still keeping full control over the system.

---

## Features

- Automatic detection of the largest disk
- Optional wipe of existing partitions
- Automatic GPT partitioning:
  - 1GB EFI partition
  - 8GB swap partition
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
- Optional KDE Plasma desktop installation
- GPU driver selection:
  - NVIDIA
  - AMD / Intel (Mesa)
- Automatic SDDM enablement when KDE is installed
- Final reboot prompt

---

## Requirements

- Arch Linux live ISO
- Internet connection
- UEFI system (EFI partition is created automatically)
- Python (already included in Arch ISO)

---

## Usage

### Boot into Arch ISO

Download the iso i left in latest release, and execute "python arch-english.py" or "python arch-spanish.py"


## How it works

The script performs the following steps:

1. Detects the largest available disk
2. Checks for existing partitions and optionally wipes them
3. Creates GPT partition table and required partitions
4. Formats partitions and mounts them
5. Installs base system with pacstrap
6. Configures system (hostname, users, passwords)
7. Installs and configures GRUB
8. Optionally installs KDE Plasma and GPU drivers
9. Prompts user to reboot

---

## Warning

This script will **erase all data on the selected disk**.

Use it only on systems where data loss is acceptable.

---

## Future improvements

- Multi-language selector at boot
- Automatic timezone and locale setup
- More desktop enviroments

---

## License

MIT License

---

## Contributing

Pull requests are welcome. If you find bugs or want new features, feel free to open an issue.