#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void run(const char* cmd) {
    printf("\n>>> Running: %s\n", cmd);
    int ret = system(cmd);
    if(ret != 0) {
        printf("Error running command. Aborting.\n");
        exit(1);
    }
}

int confirm(const char* msg) {
    char resp[4];
    while(1) {
        printf("%s (y/n): ", msg);
        scanf("%3s", resp);
        if(resp[0]=='y' || resp[0]=='Y') return 1;
        if(resp[0]=='n' || resp[0]=='N') return 0;
        printf("Invalid command, try again.\n");
    }
}

int main() {
    char disk[32];
    printf("Enter disk (example /dev/sda): ");
    scanf("%31s", disk);

    char cmd[256];

    snprintf(cmd, sizeof(cmd), "lsblk -n -o NAME,SIZE %s", disk);
    run(cmd);

    if(confirm("ALL DATA on the disk will be erased. Continue?") == 0) {
        printf("Cancelled.\n");
        exit(0);
    }

    char swap_size[16];
    printf("Enter swap size in GB (example 8): ");
    scanf("%15s", swap_size);

    // Crear particiones
    snprintf(cmd, sizeof(cmd), "sgdisk -n1:0:+1G -t1:ef00 %s", disk);
    run(cmd);
    snprintf(cmd, sizeof(cmd), "sgdisk -n2:0:+%sG -t2:8200 %s", swap_size, disk);
    run(cmd);
    snprintf(cmd, sizeof(cmd), "sgdisk -n3:0:0 -t3:8300 %s", disk);
    run(cmd);

    char p1[64], p2[64], p3[64];
    if(strstr(disk, "nvme")) {
        snprintf(p1, sizeof(p1), "%sp1", disk);
        snprintf(p2, sizeof(p2), "%sp2", disk);
        snprintf(p3, sizeof(p3), "%sp3", disk);
    } else {
        snprintf(p1, sizeof(p1), "%s1", disk);
        snprintf(p2, sizeof(p2), "%s2", disk);
        snprintf(p3, sizeof(p3), "%s3", disk);
    }

    run("mkfs.fat -F32 p1");
    snprintf(cmd, sizeof(cmd), "mkswap %s", p2);
    run(cmd);
    snprintf(cmd, sizeof(cmd), "swapon %s", p2);
    run(cmd);
    snprintf(cmd, sizeof(cmd), "mkfs.ext4 %s", p3);
    run(cmd);

    run("mount p3 /mnt");
    run("mkdir -p /mnt/boot/efi");
    snprintf(cmd, sizeof(cmd), "mount %s /mnt/boot/efi", p1);
    run(cmd);

    if(confirm("Install base system with pacstrap?") == 0) {
        run("poweroff");
        exit(0);
    }

    run("pacstrap /mnt linux linux-firmware sof-firmware base-devel grub efibootmgr vim nano networkmanager");
    run("genfstab -U /mnt >> /mnt/etc/fstab");

    char hostname[64];
    printf("Enter hostname: ");
    scanf("%63s", hostname);

    FILE* f = fopen("/mnt/etc/hostname", "w");
    if(f) {
        fprintf(f, "%s\n", hostname);
        fclose(f);
    } else {
        printf("Cannot write hostname file. Aborting.\n");
        exit(1);
    }

    printf("Set root password manually after chroot.\n");
    snprintf(cmd, sizeof(cmd), "arch-chroot /mnt /bin/bash -c 'passwd'");
    run(cmd);

    char username[32];
    printf("Enter username: ");
    scanf("%31s", username);
    snprintf(cmd, sizeof(cmd), "arch-chroot /mnt useradd -m -G wheel -s /bin/bash %s", username);
    run(cmd);

    printf("Set user password manually after chroot.\n");
    snprintf(cmd, sizeof(cmd), "arch-chroot /mnt /bin/bash -c 'passwd %s'", username);
    run(cmd);

    run("arch-chroot /mnt sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers");
    run("arch-chroot /mnt systemctl enable NetworkManager");
    snprintf(cmd, sizeof(cmd), "arch-chroot /mnt grub-install %s", disk);
    run(cmd);
    run("arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg");

    printf("Installation finished.\n");
    if(confirm("Reboot now?")) {
        run("reboot");
    }

    return 0;
}