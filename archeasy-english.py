import subprocess
import os
import sys

def run(cmd):
    print(f"\n>>> Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("Error running command. Aborting.")
        sys.exit(1)

def get_largest_disk():
    output = subprocess.check_output("lsblk -b -d -o NAME,SIZE | tail -n +2", shell=True).decode()
    disks = []
    for line in output.splitlines():
        name, size = line.split()
        disks.append((name, int(size)))
    disks.sort(key=lambda x: x[1], reverse=True)
    return disks[0][0]

def confirm(msg):
    resp = input(f"{msg} (y/n): ").lower()
    return resp == "y"

disk = get_largest_disk()
disk_path = f"/dev/{disk}"

print(f"Detected disk: {disk_path}")

if not confirm("ALL DATA on this disk will be erased. Continue?"):
    print("Cancelled.")
    sys.exit(0)

run(f"cfdisk {disk_path}")

p1 = f"{disk_path}1" if "nvme" not in disk else f"{disk_path}p1"
p2 = f"{disk_path}2" if "nvme" not in disk else f"{disk_path}p2"
p3 = f"{disk_path}3" if "nvme" not in disk else f"{disk_path}p3"

run(f"mkfs.ext4 {p3}")
run(f"mkfs.fat -F 32 {p1}")
run(f"mkswap {p2}")

run(f"mount {p3} /mnt")
run("mkdir -p /mnt/boot/efi")
run(f"mount {p1} /mnt/boot/efi")
run(f"swapon {p2}")

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

run("umount -a")

print("Installation finished.")
resp = input("Reboot now? (y/n): ")

if resp.lower() == "y":
    run("reboot")