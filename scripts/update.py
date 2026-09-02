#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一 sing-box 规则构建脚本。

功能：
1. 获取最新稳定版 sing-box（可通过 SING_BOX_BIN 指定本地二进制）。
2. 生成所有 JSON 规则源（geosite/geoip/AdGuard 下载、static 静态规则）。
3. 使用 sing-box 将 JSON 编译成 SRS，并将 AdGuard 原始文本转换成 SRS。
4. 产物输出到 SING_BOX_OUTPUT_DIR/sing-box，供 GitHub Actions 发布到 sing-box 分支。
"""

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# 常量与配置
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = REPO_ROOT / "static"

OUTPUT_ROOT = Path(os.environ.get("SING_BOX_OUTPUT_DIR", REPO_ROOT / "dist")).resolve()
RULES_DIR = OUTPUT_ROOT / "sing-box"

SING_BOX_BIN_ENV = os.environ.get("SING_BOX_BIN", "")

# 数据源 URL
GEOSITE_CN_URL = (
    "https://github.com/Accademia/Additional_Rule_For_Clash/raw/refs/heads/main/"
    "GeositeCN/GeositeCN.yaml"
)
TELEGRAM_CIDR_URL = "https://core.telegram.org/resources/cidr.txt"
GEOIP2_CN_URL = (
    "https://raw.githubusercontent.com/Hackl0us/GeoIP2-CN/refs/heads/release/"
    "CN-ip-cidr.txt"
)
ADGUARD_FILTER_LIST_URL = (
    "https://raw.githubusercontent.com/ppfeufer/adguard-filter-list/refs/heads/"
    "master/blocklist"
)
ADGUARD_DNS_FILTER_URL = (
    "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt"
)


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------

def http_get_text(url: str) -> str:
    print(f"[下载] {url}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.text


def http_download(url: str, dest: Path) -> None:
    print(f"[下载] {url} -> {dest}")
    response = requests.get(url, timeout=120, stream=True)
    response.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 256):
            if chunk:
                f.write(chunk)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_cmd(cmd, check: bool = True):
    print(f"[执行] {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, check=check, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    return result


# ---------------------------------------------------------------------------
# sing-box 获取与验证
# ---------------------------------------------------------------------------

def latest_sing_box() -> tuple[str, str]:
    """返回 (版本号, linux-amd64 资源名)。"""
    print("[sing-box] 查询 GitHub 最新稳定版 ...")
    url = "https://api.github.com/repos/SagerNet/sing-box/releases/latest"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    data = response.json()
    tag_name = data.get("tag_name", "").lstrip("v")
    if not tag_name:
        raise RuntimeError("无法从 GitHub API 获取 sing-box 最新版本号")
    asset_name = None
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if "linux-amd64.tar.gz" in name:
            asset_name = name
            break
    if not asset_name:
        raise RuntimeError(f"未找到 sing-box {tag_name} 的 linux-amd64 资源")
    print(f"[sing-box] 最新稳定版: v{tag_name}")
    return tag_name, asset_name


def resolve_sing_box_bin() -> str:
    if SING_BOX_BIN_ENV:
        bin_path = Path(SING_BOX_BIN_ENV).resolve()
        if not bin_path.exists():
            raise FileNotFoundError(f"SING_BOX_BIN 指定的文件不存在: {bin_path}")
        return str(bin_path)

    # 未显式指定时，总是下载最新稳定版 Linux amd64，保证不使用旧版本。
    version, asset_name = latest_sing_box()
    work_dir = Path(tempfile.gettempdir()) / "sing-box-builder"
    work_dir.mkdir(parents=True, exist_ok=True)
    archive = work_dir / asset_name
    download_url = (
        f"https://github.com/SagerNet/sing-box/releases/download/"
        f"v{version}/{asset_name}"
    )
    http_download(download_url, archive)

    extract_dir = work_dir / f"sing-box-{version}-linux-amd64"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(work_dir)

    binary = extract_dir / "sing-box"
    if not binary.exists():
        raise RuntimeError("解压后未找到 sing-box 二进制文件")
    binary.chmod(0o755)
    return str(binary)


def print_sing_box_version(bin_path: str) -> None:
    result = subprocess.run(
        [bin_path, "version"], capture_output=True, text=True, check=True
    )
    print("[sing-box] " + result.stdout.strip().splitlines()[0])


# ---------------------------------------------------------------------------
# 规则生成
# ---------------------------------------------------------------------------

def update_geosite_cn() -> None:
    print("[生成] geosite/cn2.json")
    content = http_get_text(GEOSITE_CN_URL)
    domains = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "DOMAIN-SUFFIX" not in line:
            continue
        parts = line.split(",")
        if len(parts) < 2:
            continue
        domain_part = parts[1]
        if "#" in domain_part:
            domain_part = domain_part.split("#", 1)[0]
        domain = domain_part.strip()
        if domain:
            domains.append(domain)

    data = {
        "version": 3,
        "rules": [{"domain_suffix": domains}],
    }
    write_json(RULES_DIR / "geosite" / "cn2.json", data)
    print(f"[完成] geosite/cn2.json，共 {len(domains)} 条")


def update_telegram_cidr() -> None:
    print("[生成] geoip/telegram.json")
    content = http_get_text(TELEGRAM_CIDR_URL)
    cidrs = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
    data = {
        "version": 3,
        "rules": [{"ip_cidr": cidrs}],
    }
    write_json(RULES_DIR / "geoip" / "telegram.json", data)
    print(f"[完成] geoip/telegram.json，共 {len(cidrs)} 条")


def update_geoip2_cn() -> None:
    print("[生成] geoip/geoip2-cn.json")
    content = http_get_text(GEOIP2_CN_URL)
    cidrs = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
    data = {
        "version": 3,
        "rules": [{"ip_cidr": cidrs}],
    }
    write_json(RULES_DIR / "geoip" / "geoip2-cn.json", data)
    print(f"[完成] geoip/geoip2-cn.json，共 {len(cidrs)} 条")


def update_adguard_filter_list() -> None:
    print("[生成] adguard_filter_list")
    content = http_get_text(ADGUARD_FILTER_LIST_URL)
    dest = RULES_DIR / "adguard_filter_list"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[完成] adguard_filter_list，{len(content)} 字符")


def update_adguard_dns_filter() -> None:
    print("[生成] adguard_dns_filter")
    content = http_get_text(ADGUARD_DNS_FILTER_URL)
    dest = RULES_DIR / "adguard_dns_filter"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[完成] adguard_dns_filter，{len(content)} 字符")


def copy_static_rules() -> None:
    if not STATIC_DIR.exists():
        print(f"[跳过] static 目录不存在: {STATIC_DIR}")
        return
    print(f"[复制] {STATIC_DIR} -> {RULES_DIR}")
    shutil.copytree(STATIC_DIR, RULES_DIR, dirs_exist_ok=True)


# ---------------------------------------------------------------------------
# 编译
# ---------------------------------------------------------------------------

def compile_all_json(bin_path: str) -> None:
    print("[编译] 所有 JSON -> SRS")
    json_files = sorted(RULES_DIR.rglob("*.json"))
    if not json_files:
        print("[警告] 未找到 JSON 文件")
        return
    for json_path in json_files:
        srs_path = json_path.with_suffix(".srs")
        cmd = [bin_path, "rule-set", "compile", str(json_path), "-o", str(srs_path)]
        run_cmd(cmd)
    print(f"[完成] 编译 {len(json_files)} 个 JSON")


def convert_adguard_files(bin_path: str) -> None:
    print("[转换] AdGuard 原始列表 -> SRS")
    raw_files = [
        RULES_DIR / "adguard_filter_list",
        RULES_DIR / "adguard_dns_filter",
    ]
    for raw_path in raw_files:
        if not raw_path.exists():
            print(f"[跳过] 不存在: {raw_path}")
            continue
        srs_path = raw_path.with_suffix(raw_path.suffix + ".srs")
        cmd = [
            bin_path,
            "rule-set",
            "convert",
            "--type",
            "adguard",
            "-o",
            str(srs_path),
            str(raw_path),
        ]
        run_cmd(cmd)
    print("[完成] AdGuard 转换")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"输出目录: {OUTPUT_ROOT}")
    if RULES_DIR.exists():
        shutil.rmtree(RULES_DIR)
    RULES_DIR.mkdir(parents=True, exist_ok=True)

    bin_path = resolve_sing_box_bin()
    print_sing_box_version(bin_path)

    update_geosite_cn()
    update_telegram_cidr()
    update_geoip2_cn()
    update_adguard_filter_list()
    update_adguard_dns_filter()
    copy_static_rules()

    compile_all_json(bin_path)
    convert_adguard_files(bin_path)

    print(f"\n构建完成，产物目录: {RULES_DIR}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"\n[错误] {exc}", file=sys.stderr)
        sys.exit(1)
