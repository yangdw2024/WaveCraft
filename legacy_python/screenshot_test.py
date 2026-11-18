import sys
import os
import time
import subprocess

exe_path = r"D:\Multiwfn\WaveCraft_GUI\dist_v2\WaveCraft.exe"
screenshot_path = r"D:\Multiwfn\WaveCraft_GUI\gui_screenshot.png"

print(f"正在启动: {exe_path}")
print(f"文件存在: {os.path.exists(exe_path)}")

try:
    proc = subprocess.Popen(exe_path, shell=False)
    print(f"进程已启动，PID: {proc.pid}")
    time.sleep(8)

    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        screenshot.save(screenshot_path)
        print(f"截图已保存: {screenshot_path}, 大小: {screenshot.size}")
    except Exception as e:
        print(f"截图失败: {e}")

    time.sleep(2)
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except:
        proc.kill()
    print("进程已关闭")

except Exception as e:
    print(f"启动失败: {e}")
    import traceback
    traceback.print_exc()
