import subprocess
import requests
import os

def convert3():
    # 1. 下载 adguard dns filer
    url = "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt"
    local_file = "sing-box/adguard_dns_filter"

    r = requests.get(url)
    with open(local_file, "w", encoding="utf-8") as f:
        f.write(r.text)

    # 2. 使用 Linux 的 sing-box 编译
    cmd = [
        "./bin/sing-box", "rule-set", "convert",
        "--type", "adguard", "sing-box/adguard_dns_filter"
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("编译成功！")
    except subprocess.CalledProcessError as e:
        print("编译失败：")
        print(e.stderr)

if __name__ == '__main__':
    convert3()
