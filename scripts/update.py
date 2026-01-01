import requests
import json
import os
import re

# 配置部分
SOURCE_URL = "https://github.com/Accademia/Additional_Rule_For_Clash/raw/refs/heads/main/GeositeCN/GeositeCN.yaml"
# 输出文件的相对路径
OUTPUT_FILE = "sing-box/geosite/cn2.json"

def download_and_parse():
    print(f"正在从 {SOURCE_URL} 下载数据...")
    try:
        response = requests.get(SOURCE_URL, timeout=30)
        response.raise_for_status()
        content = response.text
    except Exception as e:
        print(f"下载失败: {e}")
        exit(1)

    domain_list = []
    
    # 逐行处理，比直接用 yaml 库解析更灵活，因为源文件包含大量注释
    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        
        # 1. 忽略空行
        if not line:
            continue
            
        # 2. 忽略被注释掉的代码 (以 # 开头)
        if line.startswith("#"):
            continue
            
        # 3. 匹配目标行：必须包含 - DOMAIN-SUFFIX
        # 这里的逻辑是：去掉行首的 '-' 和 'DOMAIN-SUFFIX' 以及可能的 ','
        if "DOMAIN-SUFFIX" in line:
            # 数据格式示例: - DOMAIN-SUFFIX   , 115.com   # GeoSite:115
            
            # 以逗号分割，取第二部分
            parts = line.split(',')
            if len(parts) >= 2:
                domain_part = parts[1]
                
                # 去掉行尾的注释 (去掉 # 及其后面的内容)
                if '#' in domain_part:
                    domain_part = domain_part.split('#')[0]
                
                # 清理前后空格
                domain = domain_part.strip()
                
                if domain:
                    domain_list.append(domain)

    # 去重 (可选，为了保持文件精简)
    # domain_list = sorted(list(set(domain_list))) 
    # 按照你给的示例，保持原有顺序可能更好，这里我不做强制去重，直接写入
    
    print(f"提取到 {len(domain_list)} 条域名规则。")
    return domain_list

def save_to_json(domains):
    # 构建 Sing-box 格式结构
    data = {
        "version": 3,
        "rules": [
            {
                "domain_suffix": domains
            }
        ]
    }

    # 确保输出目录存在
    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建目录: {output_dir}")

    # 写入文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"文件已成功保存至: {OUTPUT_FILE}")

if __name__ == "__main__":
    domains = download_and_parse()
    save_to_json(domains)
