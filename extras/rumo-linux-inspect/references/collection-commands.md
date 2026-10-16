# Read-Only Linux Hardware Collection Commands

Run these sections separately in the interactive SSH session. Preserve each section's output in the raw record. Missing commands and permission failures are evidence; do not install replacements.

## HOST_SYSTEM

```bash
hostname
date --iso-8601=seconds 2>/dev/null || date
uname -a
cat /etc/os-release 2>/dev/null
uptime
id
systemd-detect-virt 2>/dev/null || true
getenforce 2>/dev/null || true
```

## CPU

```bash
lscpu 2>/dev/null || cat /proc/cpuinfo
lscpu -e 2>/dev/null || true
for f in /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq; do printf '%s=' "$f"; cat "$f" 2>/dev/null || echo '[unavailable]'; done
```

## MEMORY

```bash
free -h
lsmem 2>/dev/null || true
sed -n '1,30p' /proc/meminfo
command -v dmidecode >/dev/null && sudo dmidecode -t memory 2>/dev/null || true
```

## DMI_SYSTEM_BASEBOARD_BIOS

```bash
for f in /sys/class/dmi/id/sys_vendor /sys/class/dmi/id/product_name /sys/class/dmi/id/product_version /sys/class/dmi/id/product_serial /sys/class/dmi/id/product_uuid /sys/class/dmi/id/board_vendor /sys/class/dmi/id/board_name /sys/class/dmi/id/board_version /sys/class/dmi/id/board_serial /sys/class/dmi/id/bios_vendor /sys/class/dmi/id/bios_version /sys/class/dmi/id/bios_date; do printf '%s=' "$f"; cat "$f" 2>/dev/null || echo '[unavailable]'; done
command -v dmidecode >/dev/null && sudo dmidecode -t system -t baseboard -t bios -t chassis 2>/dev/null || true
```

## STORAGE_SMART_LVM_RAID

```bash
lsblk -e7 -o NAME,MODEL,SERIAL,SIZE,ROTA,RM,TYPE,FSTYPE,MOUNTPOINT,UUID 2>/dev/null || lsblk -e7
df -hT
cat /proc/partitions
cat /proc/mdstat
for d in /sys/block/*; do [ -f "$d/device/model" ] || continue; echo "--$d--"; for f in device/model device/vendor device/rev device/serial queue/logical_block_size queue/physical_block_size queue/rotational queue/scheduler; do printf '%s=' "$f"; cat "$d/$f" 2>/dev/null || echo '[unavailable]'; done; done
for d in /dev/sd? /dev/nvme?n1; do [ -b "$d" ] || continue; echo "--$d--"; udevadm info --query=property --name="$d" 2>/dev/null | grep -E '^(ID_BUS|ID_MODEL|ID_SERIAL|ID_VENDOR|ID_ATA_ROTATION_RATE_RPM)='; done
command -v nvme >/dev/null && nvme list 2>/dev/null || true
command -v pvs >/dev/null && pvs 2>/dev/null || true
command -v vgs >/dev/null && vgs 2>/dev/null || true
command -v lvs >/dev/null && lvs 2>/dev/null || true
```

For each detected disk, run SMART only when `smartctl` is already installed. Replace the device names with those actually returned by `lsblk`.

```bash
command -v smartctl >/dev/null && sudo smartctl -H -i /dev/sda 2>/dev/null || true
command -v smartctl >/dev/null && sudo smartctl -H -i /dev/sdb 2>/dev/null || true
```

## NETWORK

```bash
ip -br addr
ip -br link
ip route
ip -s link
for i in /sys/class/net/*; do n=$(basename "$i"); echo "--$n--"; printf 'mac='; cat "$i/address" 2>/dev/null || true; printf 'state='; cat "$i/operstate" 2>/dev/null || true; printf 'speed='; cat "$i/speed" 2>/dev/null || true; printf 'duplex='; cat "$i/duplex" 2>/dev/null || true; printf 'mtu='; cat "$i/mtu" 2>/dev/null || true; printf 'rx_errors='; cat "$i/statistics/rx_errors" 2>/dev/null || true; printf 'rx_dropped='; cat "$i/statistics/rx_dropped" 2>/dev/null || true; printf 'tx_errors='; cat "$i/statistics/tx_errors" 2>/dev/null || true; printf 'tx_dropped='; cat "$i/statistics/tx_dropped" 2>/dev/null || true; printf 'driver='; readlink -f "$i/device/driver" 2>/dev/null || true; done
```

For each confirmed online Ethernet interface, use its actual name:

```bash
command -v ethtool >/dev/null && ethtool eth0 2>/dev/null || true
command -v ethtool >/dev/null && ethtool -i eth0 2>/dev/null || true
```

## PCI_USB_THERMAL_TIME

```bash
command -v lspci >/dev/null && lspci -nnk 2>/dev/null || true
command -v lsusb >/dev/null && lsusb 2>/dev/null || true
for z in /sys/class/thermal/thermal_zone*; do [ -d "$z" ] || continue; printf '%s type=' "$z"; cat "$z/type" 2>/dev/null || true; printf 'temp='; cat "$z/temp" 2>/dev/null || true; done
command -v sensors >/dev/null && sensors 2>/dev/null || true
timedatectl 2>/dev/null || true
```
