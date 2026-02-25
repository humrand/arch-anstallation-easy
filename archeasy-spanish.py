import subprocess
import sys

def run(cmd):
    print(f"\n>>> Ejecutando: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("Error al ejecutar el comando. Abortando.")
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

# Detectar si hay particiones
partitions = subprocess.check_output(f"lsblk -n -o NAME {disk_path}", shell=True).decode().splitlines()[1:]
if partitions:
    print(f"Se detectaron particiones en {disk_path}: {', '.join(partitions)}")
    if confirm("¿Deseas borrar todas las particiones existentes?"):
        run(f"sgdisk -Z {disk_path}")
    else:
        print("No se puede continuar con particiones existentes. Abortando.")
        sys.exit(0)

if not confirm(f"SE BORRARÁ TODO EN {disk_path}. ¿Continuar?"):
    print("Cancelado.")
    sys.exit(0)

run(f"sgdisk -n1:0:+1G -t1:ef00 {disk_path}")
run(f"sgdisk -n2:0:+8G -t2:8200 {disk_path}")
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

if not confirm("¿Instalar el sistema base con pacstrap?"):
    run("poweroff")
    sys.exit(0)

run("pacstrap /mnt linux linux-firmware sof-firmware base-devel grub efibootmgr vim nano networkmanager")
run("genfstab -U /mnt >> /mnt/etc/fstab")

hostname = input("Ingresa el nombre del equipo: ")
with open("/mnt/etc/hostname", "w") as f:
    f.write(hostname + "\n")

def chroot(cmd):
    run(f"arch-chroot /mnt /bin/bash -c \"{cmd}\"")

print("Configura la contraseña de root:")
chroot("passwd")

username = input("Ingresa el nombre de usuario: ")
chroot(f"useradd -m -G wheel -s /bin/bash {username}")
print("Configura la contraseña del usuario:")
chroot(f"passwd {username}")

chroot("sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")
chroot("systemctl enable NetworkManager")

run(f"arch-chroot /mnt grub-install {disk_path}")
run("arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg")

if confirm("¿Deseas instalar KDE Plasma?"):
    chroot("pacman -S --noconfirm xorg-server xorg-apps xorg-xinit xorg-xrandr")
    chroot("pacman -S --noconfirm xf86-input-libinput")
    gpu = input("Selecciona GPU: 1 para NVIDIA, 2 para AMD/Intel: ")
    if gpu == "1":
        chroot("pacman -S --noconfirm nvidia nvidia-utils nvidia-settings")
    elif gpu == "2":
        chroot("pacman -S --noconfirm mesa")
    chroot("pacman -S --noconfirm plasma-meta")
    chroot("pacman -S --noconfirm konsole dolphin ark kate plasma-nm")
    chroot("pacman -S --noconfirm sddm")
    chroot("systemctl enable sddm")

print("\nInstalación finalizada.")
resp = input("¿Reiniciar ahora? (s/n): ")
if resp.lower() == "s":
    run("reboot")
