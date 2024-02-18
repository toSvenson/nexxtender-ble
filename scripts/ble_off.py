import os

result = os.system('bluetoothctl power off')

if result == 0:
    exit(0)
else:
    exit(1)
