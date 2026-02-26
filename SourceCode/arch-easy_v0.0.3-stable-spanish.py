import subprocess
import sys

# MIT LICENSE, YOU CAN USE IT BUT YOU GOTTA GIVE ME CREDITS,
# made by humrand https://github.com/humrand/arch-anstallation-easy
# DO NOT REMOVE THIS FROM YOUR CODE IF YOU USE IT TO MODIFY IT.


def ejecutar(cmd):
    print(f"\n>>> Ejecutando: {cmd}")
    resultado = subprocess.run(cmd, shell=True)
    if resultado.returncode != 0:
        print("Error al ejecutar el comando. Abortando.")
        sys.exit(1)

def listar_discos():
    salida = subprocess.check_output("lsblk -b -d -o NAME,SIZE | tail -n +2", shell=True).decode()
    discos = []
    for linea in salida.splitlines():
        nombre, size = linea.split()
        size_gb = int(size) // (1024**3)
        discos.append((nombre, size_gb))
    return discos

def elegir_disco():
    discos = listar_discos()
    print("Discos disponibles:")
    for i, (nombre, size) in enumerate(discos):
        print(f"{i+1}. /dev/{nombre} ({size} GB)")
    while True:
        try:
            eleccion = int(input("Selecciona el número del disco: "))
            if 1 <= eleccion <= len(discos):
                return discos[eleccion-1][0]
        except ValueError:
            pass
        print("Comando inválido, intenta de nuevo.")

def confirmar(msg):
    while True:
        resp = input(f"{msg} (s/n): ").lower()
        if resp in ("s", "n"):
            return resp == "s"
        print("Comando inválido, intenta de nuevo.")

def elegir_escritorio():
    while True:
        eleccion = input("Elige escritorio: 1 = KDE Plasma, 2 = Cinnamon: ")
        if eleccion in ("1", "2"):
            return eleccion
        print("Comando inválido, intenta de nuevo.")

def elegir_gpu():
    while True:
        gpu = input("Selecciona GPU: 1 para NVIDIA, 2 para AMD/Intel (ENTER para omitir): ")
        if gpu in ("1", "2", ""):
            return gpu
        print("Comando inválido, intenta de nuevo.")

disco = elegir_disco()
ruta_disco = f"/dev/{disco}"
print(f"Disco seleccionado: {ruta_disco}")

particiones = subprocess.check_output(f"lsblk -n -o NAME {ruta_disco}", shell=True).decode().splitlines()[1:]
if particiones:
    print(f"Particiones detectadas en {ruta_disco}: {', '.join(particiones)}")
    if confirmar("¿Deseas borrar todas las particiones existentes?"):
        ejecutar(f"sgdisk -Z {ruta_disco}")
    else:
        print("No se puede continuar con particiones existentes. Abortando.")
        sys.exit(0)

if not confirmar(f"SE BORRARÁ TODO EN {ruta_disco}. ¿Continuar?"):
    print("Cancelado.")
    sys.exit(0)

swap_size = input("Ingresa tamaño del swap en GB (ejemplo 8): ")

ejecutar(f"sgdisk -n1:0:+1G -t1:ef00 {ruta_disco}")
ejecutar(f"sgdisk -n2:0:+{swap_size}G -t2:8200 {ruta_disco}")
ejecutar(f"sgdisk -n3:0:0 -t3:8300 {ruta_disco}")

p1 = f"{ruta_disco}1" if "nvme" not in disco else f"{ruta_disco}p1"
p2 = f"{ruta_disco}2" if "nvme" not in disco else f"{ruta_disco}p2"
p3 = f"{ruta_disco}3" if "nvme" not in disco else f"{ruta_disco}p3"

ejecutar(f"mkfs.fat -F32 {p1}")
ejecutar(f"mkswap {p2}")
ejecutar(f"swapon {p2}")
ejecutar(f"mkfs.ext4 {p3}")

ejecutar(f"mount {p3} /mnt")
ejecutar("mkdir -p /mnt/boot/efi")
ejecutar(f"mount {p1} /mnt/boot/efi")

if not confirmar("¿Instalar sistema base con pacstrap?"):
    ejecutar("poweroff")
    sys.exit(0)

ejecutar("pacstrap /mnt linux linux-firmware sof-firmware base-devel grub efibootmgr vim nano networkmanager")
ejecutar("genfstab -U /mnt >> /mnt/etc/fstab")

hostname = input("Ingresa el nombre del equipo: ")
with open("/mnt/etc/hostname", "w") as f:
    f.write(hostname + "\n")

def chroot(cmd):
    ejecutar(f"arch-chroot /mnt /bin/bash -c \"{cmd}\"")

print("Configura la contraseña de root:")
chroot("passwd")

usuario = input("Ingresa el nombre de usuario: ")
chroot(f"useradd -m -G wheel -s /bin/bash {usuario}")
print("Configura la contraseña del usuario:")
chroot(f"passwd {usuario}")

chroot("sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")
chroot("systemctl enable NetworkManager")

ejecutar(f"arch-chroot /mnt grub-install {ruta_disco}")
ejecutar("arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg")

gpu = elegir_gpu()
if gpu == "1":
    chroot("pacman -S --noconfirm nvidia nvidia-utils nvidia-settings")
elif gpu == "2":
    chroot("pacman -S --noconfirm mesa")

if confirmar("¿Deseas un entorno de escritorio?"):
    escritorio = elegir_escritorio()
    if escritorio == "1":
        chroot("pacman -S --noconfirm xorg-server xorg-apps xorg-xinit xorg-xrandr xf86-input-libinput")
        chroot("pacman -S --noconfirm plasma-meta konsole dolphin ark kate plasma-nm firefox")
        chroot("pacman -S --noconfirm sddm")
        chroot("systemctl enable sddm")
    elif escritorio == "2":
        chroot("pacman -S --noconfirm cinnamon lightdm lightdm-gtk-greeter xorg")
        chroot("pacman -S --noconfirm alacritty firefox")
        chroot("systemctl enable lightdm")

print("\nInstalación finalizada.")
if confirmar("¿Reiniciar ahora?"):
    ejecutar("reboot")
