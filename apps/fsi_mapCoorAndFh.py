import os
import time

import workPath

item = 0
while 1 < 3:
    item += 1
    print("Times of Run" + str(item))
    os.system("python3 " + workPath.FSI_path + "generateInput.py")
    time.sleep(2.5)