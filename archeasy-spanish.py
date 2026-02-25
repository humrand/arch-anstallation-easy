import subprocess
import os
import sys

def run(cmd):
    print(f"\n>>> Ejecutando: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("Error ejecutando comando. Abortando.")
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
    resp = input(f"{msg} (s/n): ").lower()
    return resp == "s"

disk = get_largest_disk()
disk_path = f"/dev/{disk}"

print(f"Disco detectado: {disk_path}")

if not confirm("Se borrará TODO el disco. ¿Continuar?"):
    print("Cancelado.")
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

if not confirm("¿Instalar sistema base con pacstrap?"):
    run("poweroff")
    sys.exit(0)

run("pacstrap /mnt linux linux-firmware sof-firmware base-devel grub efibootmgr vim nano networkmanager")

run("genfstab -U /mnt >> /mnt/etc/fstab")

hostname = input("Nombre del equipo: ")
with open("/mnt/etc/hostname", "w") as f:
    f.write(hostname + "\n")

def chroot(cmd):
    run(f"arch-chroot /mnt /bin/bash -c \"{cmd}\"")

print("Introduce contraseña root:")
chroot("passwd")

username = input("Nombre de usuario: ")
chroot(f"useradd -m -G wheel -s /bin/bash {username}")
print("Contraseña del usuario:")
chroot(f"passwd {username}")

chroot("sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")

chroot("systemctl enable NetworkManager")

run(f"arch-chroot /mnt grub-install {disk_path}")
run("arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg")

run("umount -a")

print("Instalación terminada.")
resp = input("¿Reiniciar ahora? (s/n): ")

if resp.lower() == "s":
    run("reboot")