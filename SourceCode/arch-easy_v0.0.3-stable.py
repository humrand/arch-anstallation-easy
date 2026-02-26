import subprocess
import sys

# MIT LICENSE, YOU CAN USE IT BUT YOU GOTTA GIVE ME CREDITS,
# made by humrand https://github.com/humrand/arch-anstallation-easy
# DO NOT REMOVE THIS FROM YOUR CODE IF YOU USE IT TO MODIFY IT.


def run(cmd):
    print(f"\n>>> Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("Error running command. Aborting.")
        sys.exit(1)

def list_disks():
    output = subprocess.check_output("lsblk -b -d -o NAME,SIZE | tail -n +2", shell=True).decode()
    disks = []
    for line in output.splitlines():
        name, size = line.split()
        size_gb = int(size) // (1024**3)
        disks.append((name, size_gb))
    return disks

def choose_disk():
    disks = list_disks()
    print("Available disks:")
    for i, (name, size) in enumerate(disks):
        print(f"{i+1}. /dev/{name} ({size} GB)")
    while True:
        try:
            choice = int(input("Select disk number: "))
            if 1 <= choice <= len(disks):
                return disks[choice-1][0]
        except ValueError:
            pass
        print("Invalid command, try again.")

def confirm(msg):
    while True:
        resp = input(f"{msg} (y/n): ").lower()
        if resp in ("y", "n"):
            return resp == "y"
        print("Invalid command, try again.")

def choose_desktop():
    while True:
        choice = input("Choose desktop: 1 = KDE Plasma, 2 = Cinnamon: ")
        if choice in ("1", "2"):
            return choice
        print("Invalid command, try again.")

def choose_gpu():
    while True:
        gpu = input("Select GPU: 1 for NVIDIA, 2 for AMD/Intel (or press ENTER to skip): ")
        if gpu in ("1", "2", ""):
            return gpu
        print("Invalid command, try again.")

disk = choose_disk()
disk_path = f"/dev/{disk}"
print(f"Selected disk: {disk_path}")

partitions = subprocess.check_output(f"lsblk -n -o NAME {disk_path}", shell=True).decode().splitlines()[1:]
if partitions:
    print(f"Partitions detected on {disk_path}: {', '.join(partitions)}")
    if confirm("Do you want to erase all existing partitions?"):
        run(f"sgdisk -Z {disk_path}")
    else:
        print("Cannot continue with existing partitions. Aborting.")
        sys.exit(0)

if not confirm(f"ALL DATA on {disk_path} will be erased. Continue?"):
    print("Cancelled.")
    sys.exit(0)

swap_size = input("Enter swap size in GB (example 8): ")

run(f"sgdisk -n1:0:+1G -t1:ef00 {disk_path}")
run(f"sgdisk -n2:0:+{swap_size}G -t2:8200 {disk_path}")
run(f"sgdisk -n3:0:0 -t3:8300 {disk_path}")

p1 = f"{disk_path}1" if "nvme" not in disk else f"{disk_path}p1"
p2 = f"{disk_path}2" if "nvme" not in disk else f"{disk_path}p2"
p3 = f"{disk_path}3" if "nvme" not in disk else f"{disk_path}p3"

run(f"mkfs.fat -F32 {p1}")
run(f"mkswap {p2}")
run(f"swapon {p2}")
run(f"mkfs.ext4 {p3}")

run(f"mount {p3} /mnt")
run("mkdir -p /mnt/boot/efi")
run(f"mount {p1} /mnt/boot/efi")

if not confirm("Install base system with pacstrap?"):
    run("poweroff")
    sys.exit(0)

run("pacstrap /mnt linux linux-firmware sof-firmware base-devel grub efibootmgr vim nano networkmanager")
run("genfstab -U /mnt >> /mnt/etc/fstab")

hostname = input("Enter hostname: ")
with open("/mnt/etc/hostname", "w") as f:
    f.write(hostname + "\n")

def chroot(cmd):
    run(f"arch-chroot /mnt /bin/bash -c \"{cmd}\"")

print("Set root password:")
chroot("passwd")

username = input("Enter username: ")
chroot(f"useradd -m -G wheel -s /bin/bash {username}")
print("Set user password:")
chroot(f"passwd {username}")

chroot("sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")
chroot("systemctl enable NetworkManager")

run(f"arch-chroot /mnt grub-install {disk_path}")
run("arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg")

gpu = choose_gpu()
if gpu == "1":
    chroot("pacman -S --noconfirm nvidia nvidia-utils nvidia-settings")
elif gpu == "2":
    chroot("pacman -S --noconfirm mesa")

if confirm("Do you want a desktop environment?"):
    desktop_choice = choose_desktop()
    if desktop_choice == "1":
        chroot("pacman -S --noconfirm xorg-server xorg-apps xorg-xinit xorg-xrandr xf86-input-libinput")
        chroot("pacman -S --noconfirm plasma-meta konsole dolphin ark kate plasma-nm firefox")
        chroot("pacman -S --noconfirm sddm")
        chroot("systemctl enable sddm")
    elif desktop_choice == "2":
        chroot("pacman -S --noconfirm cinnamon lightdm lightdm-gtk-greeter xorg")
        chroot("pacman -S --noconfirm alacritty firefox")
        chroot("systemctl enable lightdm")

print("\nInstallation finished.")
resp = confirm("Reboot now?")
if resp:
    run("reboot")
