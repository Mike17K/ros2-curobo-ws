# if working in container and permision for opening visuals is denied

xhost +local:root

sudo sysctl -w net.core.rmem_max=2147483647
sudo sysctl -w net.core.rmem_default=2147483647
sudo sysctl -w net.core.wmem_max=2147483647
sudo sysctl -w net.core.wmem_default=2147483647

if the iox-roudi not running map the /tmp to the containers /tmp
