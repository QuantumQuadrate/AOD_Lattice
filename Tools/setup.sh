sudo ifconfig eno4 192.168.40.1 netmask 255.255.255.0 up
sudo ifconfig eno4 mtu 9000
sudo sysctl -w net.core.wmem_max=24862979
