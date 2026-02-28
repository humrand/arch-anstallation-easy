import subprocess
import sys
import re
from datetime import datetime

LOG_FILE = "/mnt/install_log.txt"
def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass

def run(cmd, ignore_error=False):
    log(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        log(f"ERROR: Command failed: {cmd}")
        if not ignore_error:
            print("Command failed. Aborting.")
            sys.exit(1)

def confirm(msg):
    while True:
        resp = input(f"{msg} (y/n): ").lower()
        if resp in ("y", "n"):
            return resp == "y"
        print("Invalid command, try again.")

def valid_name(name):
    return re.match(r"^[a-zA-Z0-9_-]{1,32}$", name)

def input_validated(prompt, validator, error_msg):
    while True:
        val = input(prompt)
        if validator(val):
            return val
        print(error_msg)

def valid_swap(size_str):
    return re.match(r"^\d+$", size_str) and int(size_str) > 0

lang = None
while True:
    print("Select language / Seleccione idioma: 1 = English, 2 = Español")
    choice = input("> ")
    if choice == "1":
        lang = "en"
        break
    elif choice == "2":
        lang = "es"
        break
    else:
        print("Invalid command / Comando inválido")

def L(msg_en, msg_es):
    return msg_en if lang=="en" else msg_es

hostname = input_validated(L("Enter hostname: ","Ingrese el nombre del equipo: "), valid_name, L("Invalid hostname.","Nombre inválido."))
username = input_validated(L("Enter username: ","Ingrese nombre de usuario: "), valid_name, L("Invalid username.","Usuario inválido."))
root_pass = input(L("Enter root password: ","Ingrese contraseña de root: "))
user_pass = input(L("Enter user password: ","Ingrese contraseña de usuario: "))

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
    print(L("Available disks:","Discos disponibles:"))
    for i, (name, size) in enumerate(disks):
        print(f"{i+1}. /dev/{name} ({size} GB)")
    while True:
        choice = input(L("Select disk number: ","Seleccione número de disco: "))
        if choice.isdigit() and 1 <= int(choice) <= len(disks):
            return disks[int(choice)-1][0]
        print(L("Invalid command, try again.","Comando inválido, intente de nuevo."))

disk = choose_disk()
disk_path = f"/dev/{disk}"
log(f"{L('Selected disk','Disco seleccionado')}: {disk_path}")

partitions = subprocess.check_output(f"lsblk -n -o NAME {disk_path}", shell=True).decode().splitlines()[1:]
if partitions:
    print(f"{L('Partitions detected','Particiones detectadas')} {disk_path}: {', '.join(partitions)}")
    if confirm(L("Do you want to erase all existing partitions?","Desea borrar todas las particiones existentes?")):
        run(f"sgdisk -Z {disk_path}")
    else:
        print(L("Cannot continue with existing partitions. Aborting.","No se puede continuar con particiones existentes. Abortando."))
        sys.exit(0)

if not confirm(L(f"ALL DATA on {disk_path} will be erased. Continue?","TODO EL CONTENIDO de {disk_path} se borrará. Continuar?")):
    print(L("Cancelled.","Cancelado."))
    sys.exit(0)

swap_size = input_validated(L("Enter swap size in GB (example 8): ","Ingrese tamaño de swap en GB (ej 8): "), valid_swap, L("Invalid swap size.","Tamaño de swap inválido."))

log(L("Creating partitions...","Creando particiones..."))
run(f"sgdisk -n1:0:+1G -t1:ef00 {disk_path}")
run(f"sgdisk -n2:0:+{swap_size}G -t2:8200 {disk_path}")
run(f"sgdisk -n3:0:0 -t3:8300 {disk_path}")

p1 = f"{disk_path}1" if "nvme" not in disk else f"{disk_path}p1"
p2 = f"{disk_path}2" if "nvme" not in disk else f"{disk_path}p2"
p3 = f"{disk_path}3" if "nvme" not in disk else f"{disk_path}p3"

log(L("Formatting partitions...","Formateando particiones..."))
run(f"mkfs.fat -F32 {p1}")
run(f"mkswap {p2}")
run(f"swapon {p2}")
run(f"mkfs.ext4 {p3}")

log(L("Mounting partitions...","Montando particiones..."))
run(f"mount {p3} /mnt")
run("mkdir -p /mnt/boot/efi")
run(f"mount {p1} /mnt/boot/efi")

if not confirm(L("Install base system with pacstrap?","Instalar sistema base con pacstrap?")):
    run("poweroff")
    sys.exit(0)

log(L("Installing base system...","Instalando sistema base..."))
run("pacstrap /mnt linux linux-firmware sof-firmware base-devel grub efibootmgr vim nano networkmanager")
run("genfstab -U /mnt >> /mnt/etc/fstab")

def chroot(cmd):
    run(f"arch-chroot /mnt /bin/bash -c \"{cmd}\"")

log(L("Configuring system...","Configurando sistema..."))
with open("/mnt/etc/hostname", "w") as f:
    f.write(hostname + "\n")

chroot(f"echo '{root_pass}' | passwd --stdin")
chroot(f"useradd -m -G wheel -s /bin/bash {username}")
chroot(f"echo '{user_pass}' | passwd --stdin {username}")
chroot("sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")
chroot("systemctl enable NetworkManager")

log(L("Installing GRUB...","Instalando GRUB..."))
run(f"arch-chroot /mnt grub-install {disk_path}")
run("arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg")

if confirm(L("Do you want a desktop environment?","Desea instalar entorno de escritorio?")):
    while True:
        desktop_choice = input(L("Choose desktop: 1 = KDE Plasma, 2 = Cinnamon: ","Seleccione escritorio: 1 = KDE Plasma, 2 = Cinnamon: "))
        if desktop_choice in ("1","2"):
            break
        print(L("Invalid command, try again.","Comando inválido, intente de nuevo."))

    log(L("Installing Xorg and desktop packages...","Instalando Xorg y paquetes de escritorio..."))
    chroot("pacman -S --noconfirm xorg-server xorg-apps xorg-xinit xorg-xrandr xf86-input-libinput")
    if desktop_choice=="1":
        chroot("pacman -S --noconfirm plasma-meta konsole dolphin ark kate plasma-nm firefox")
        chroot("pacman -S --noconfirm sddm")
        chroot("systemctl enable sddm")
    elif desktop_choice=="2":
        chroot("pacman -S --noconfirm cinnamon lightdm lightdm-gtk-greeter alacritty firefox")
        chroot("systemctl enable lightdm")

log(L("Installation finished.","Instalación finalizada."))
if confirm(L("Reboot now?","Reiniciar ahora?")):
    run("reboot")
