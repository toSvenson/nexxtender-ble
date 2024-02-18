import os

result = os.system('bluetoothctl power on')

if result == 0:
    exit(0)
else:
    exit(1)
