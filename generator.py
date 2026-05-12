#!/usr/bin/env python3
"""
Генератор RULE-SET для Shadowrocket.
Проверяет доступность доменов и сохраняет:
- direct.txt — доступные домены (DIRECT)
- proxy.txt — недоступные домены (PROXY)
- ShadowVoice_Live.conf — маленький конфиг, ссылающийся на эти файлы
"""

import os
import re
import json
import sys
import requests
import dns.resolver
from datetime import datetime
from typing import List, Tuple, Set, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== НАСТРОЙКИ ==========
RULE_SET_URLS = {
    "ru": [
        "https://raw.githubusercontent.com/hydraponique/roscomvpn-geoip/refs/heads/release/text/direct.txt",
        "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/meta/geo/geoip/classical/ru.list",
    ],
    "foreign": [
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Google/Google.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/YouTube/YouTube.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Instagram/Instagram.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/TikTok/TikTok.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Twitter/Twitter.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/OpenAI/OpenAI.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Telegram/Telegram.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Netflix/Netflix.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Discord/Discord.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/GitHub/GitHub.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Spotify/Spotify.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Twitch/Twitch.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Reddit/Reddit.list",
    ],
    "community": [
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_community.list",
    ],
    "ipchecker": [
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_ipchecker.list",
    ],
    "geo_detect": [
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_geo_detect.list",
    ],
}

FORCE_DIRECT = {
    "gosuslugi.ru", "tbank.ru", "sberbank.ru", "vtb.ru",
    "alfabank.ru", "mail.ru", "yandex.ru", "ya.ru"
}

FORCE_PROXY = {
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "youtube.com", "google.com", "gmail.com"
}

TIMEOUT = 5
THREADS = 30
MAX_DOMAINS = 800

# Файлы
TEMPLATE_FILE = "template.conf"
OUTPUT_FILE = "ShadowVoice_Live.conf"
DIRECT_FILE = "direct.txt"
PROXY_FILE = "proxy.txt"
DOMAINS_CACHE_FILE = "domains_cache.json"

def load_cached_domains() -> Dict[str, Set[str]]:
    if os.path.exists(DOMAINS_CACHE_FILE):
        with open(DOMAINS_CACHE_FILE, "r") as f:
            data = json.load(f)
            return {
                "direct": set(data.get("direct", [])),
                "proxy": set(data.get("proxy", [])),
            }
    return {"direct": set(), "proxy": set()}

def save_cached_domains(direct: Set[str], proxy: Set[str]):
    with open(DOMAINS_CACHE_FILE, "w") as f:
        json.dump({
            "direct": list(direct),
            "proxy": list(proxy),
        }, f, indent=2)

def save_rule_set(direct: Set[str], proxy: Set[str]):
    """Сохраняет RULE-SET файлы для Shadowrocket"""
    with open(DIRECT_FILE, "w") as f:
        for d in sorted(direct):
            f.write(f"DOMAIN-SUFFIX,{d},DIRECT\n")
    with open(PROXY_FILE, "w") as f:
        for d in sorted(proxy):
            f.write(f"DOMAIN-SUFFIX,{d},PROXY\n")
    print(f"💾 Сохранено: {len(direct)} доменов в {DIRECT_FILE}, {len(proxy)} в {PROXY_FILE}")

def download_list(url: str) -> List[str]:
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return []
        content = r.text
        domains = set()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith(('#', ';', '//')):
                continue
            match = re.search(r'DOMAIN(?:-SUFFIX)?,([a-zA-Z0-9.-]+)', line)
            if match:
                domain = match.group(1).lower()
                if '*' not in domain and not re.match(r'^\d+\.\d+\.\d+\.\d+$', domain):
                    domains.add(domain)
        return list(domains)
    except Exception as e:
        print(f"  ❌ Ошибка загрузки: {e}")
        return []

def is_domain_reachable(domain: str) -> bool:
    if len(domain) > 100 or '..' in domain:
        return False
    try:
        dns.resolver.resolve(domain, 'A', lifetime=TIMEOUT)
        return True
    except:
        pass
    try:
        r = requests.get(f"https://{domain}", timeout=TIMEOUT, verify=False)
        if r.status_code < 500:
            return True
    except:
        pass
    return False

def check_domains(domains: List[str]) -> Tuple[List[str], List[str]]:
    direct = []
    proxy = []
    print(f"\n🔍 Проверка {len(domains)} доменов...")
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        future_to_domain = {executor.submit(is_domain_reachable, d): d for d in domains}
        for i, future in enumerate(as_completed(future_to_domain), 1):
            domain = future_to_domain[future]
            try:
                reachable = future.result()
                if domain in FORCE_DIRECT:
                    direct.append(domain)
                elif domain in FORCE_PROXY:
                    proxy.append(domain)
                elif reachable:
                    direct.append(domain)
                else:
                    proxy.append(domain)
            except:
                proxy.append(domain)
            if i % 100 == 0:
                print(f"  Прогресс: {i}/{len(domains)}")
    return direct, proxy

def build_config() -> str:
    """Генерирует маленький конфиг, ссылающийся на RULE-SET файлы"""
    repo_base = "https://raw.githubusercontent.com/PAE16/shadowvoice-config/main"
    
    config = f"""#!name=ShadowVoice_Live
#!desc=Adaptive config. Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[General]
bypass-system = true
ipv6 = false
prefer-ipv6 = false
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com
tun-excluded-routes = 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.0.0.0/24, 192.0.2.0/24, 192.88.99.0/24, 192.168.0.0/16, 198.51.100.0/24, 203.0.113.0/24, 224.0.0.0/4, 255.255.255.255/32, 239.255.255.250/32
dns-server = system
dns-direct-system = true
dns-direct-fallback-proxy = false
private-ip-answer = true
use-local-host-item-for-proxy = false
icmp-auto-reply = false
always-reject-url-rewrite = false
udp-policy-not-supported-behaviour = REJECT

[Rule]

# Apple Local
IP-CIDR,224.0.0.0/4,DIRECT
IP-CIDR,239.0.0.0/8,DIRECT
IP-CIDR,169.254.0.0/16,DIRECT
DOMAIN-SUFFIX,local,DIRECT
AND,((PROTOCOL,UDP),(DST-PORT,5353)),DIRECT
AND,((PROTOCOL,UDP),(DST-PORT,5350)),DIRECT
AND,((PROTOCOL,UDP),(DST-PORT,17500)),DIRECT
AND,((PROTOCOL,UDP),(DST-PORT,17501)),DIRECT

# QUIC Block
AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP

# Critical Russian Systems (always DIRECT)
DOMAIN-SUFFIX,gosuslugi.ru,DIRECT
DOMAIN-SUFFIX,gu-st.ru,DIRECT
DOMAIN-SUFFIX,esia.gosuslugi.ru,DIRECT
DOMAIN-SUFFIX,tbank.ru,DIRECT
DOMAIN-SUFFIX,sberbank.ru,DIRECT
DOMAIN-SUFFIX,vtb.ru,DIRECT
DOMAIN-SUFFIX,alfabank.ru,DIRECT
DOMAIN,vstu.ru,DIRECT
DOMAIN,volstu.ru,DIRECT

# Auto-generated RULE-SET
RULE-SET,{repo_base}/direct.txt,DIRECT
RULE-SET,{repo_base}/proxy.txt,PROXY

# Apple Services (PROXY)
IP-CIDR,17.0.0.0/8,PROXY,no-resolve
DOMAIN-SUFFIX,icloud.com,PROXY
DOMAIN-SUFFIX,icloud-content.com,PROXY
DOMAIN,api.push.apple.com,PROXY
DOMAIN-SUFFIX,apple-relay.akamaized.net,PROXY
DOMAIN-SUFFIX,apple-relay.apple.com,PROXY

# Foreign services (fallback)
DOMAIN-SUFFIX,google.com,PROXY
DOMAIN-SUFFIX,youtube.com,PROXY
DOMAIN-SUFFIX,instagram.com,PROXY
DOMAIN-SUFFIX,facebook.com,PROXY
DOMAIN-SUFFIX,twitter.com,PROXY
DOMAIN-SUFFIX,t.me,PROXY
DOMAIN-SUFFIX,telegram.org,PROXY
DOMAIN-SUFFIX,tiktok.com,PROXY
DOMAIN-SUFFIX,openai.com,PROXY
DOMAIN-SUFFIX,chatgpt.com,PROXY
DOMAIN-SUFFIX,reddit.com,PROXY
DOMAIN-SUFFIX,discord.com,PROXY
DOMAIN-SUFFIX,github.com,PROXY
DOMAIN-SUFFIX,netflix.com,PROXY
DOMAIN-SUFFIX,spotify.com,PROXY
DOMAIN-SUFFIX,twitch.tv,PROXY
DOMAIN-SUFFIX,zoom.us,PROXY

# GeoIP
GEOIP,RU,DIRECT

# Local networks
IP-CIDR,192.168.0.0/16,DIRECT
IP-CIDR,10.0.0.0/8,DIRECT
IP-CIDR,172.16.0.0/12,DIRECT
IP-CIDR,127.0.0.0/8,DIRECT

# Global default
FINAL,PROXY

[Host]
localhost = 127.0.0.1

[URL Rewrite]
^http://.*$ https://$0 302

[MITM]
hostname = *yandex*, *vk*, *google*, *youtube*, *telegram*, *tiktok*, *openai*, *chatgpt*
"""
    return config

def main():
    print("=" * 60)
    print("🚀 Генератор RULE-SET для Shadowrocket")
    print("=" * 60)

    # Загружаем кэш
    cache = load_cached_domains()
    print(f"\n📦 Загружено из кэша: DIRECT={len(cache['direct'])}, PROXY={len(cache['proxy'])}")

    # Скачиваем новые домены
    all_domains = set()
    for source_type, urls in RULE_SET_URLS.items():
        print(f"\n📥 Скачиваем {source_type.upper()} RULE-SET:")
        for url in urls:
            print(f"  Загрузка {url}...")
            domains = download_list(url)
            print(f"    Найдено {len(domains)} доменов")
            all_domains.update(domains)

    # Проверяем только новые домены
    existing_domains = cache["direct"] | cache["proxy"]
    new_domains = [d for d in all_domains if d not in existing_domains]

    print(f"\n📊 Всего уникальных доменов: {len(all_domains)}")
    print(f"📊 Уже в кэше: {len(existing_domains)}")
    print(f"📊 Новых: {len(new_domains)}")

    if new_domains:
        if len(new_domains) > MAX_DOMAINS:
            new_domains = new_domains[:MAX_DOMAINS]
        new_direct, new_proxy = check_domains(new_domains)
        cache["direct"].update(new_direct)
        cache["proxy"].update(new_proxy)
    else:
        print("\n✅ Новых доменов нет")

    # Сохраняем
    save_cached_domains(cache["direct"], cache["proxy"])
    save_rule_set(cache["direct"], cache["proxy"])

    # Генерируем маленький конфиг
    with open(OUTPUT_FILE, "w") as f:
        f.write(build_config())

    print(f"\n✅ Готово!")
    print(f"📊 DIRECT: {len(cache['direct'])} доменов → {DIRECT_FILE}")
    print(f"📊 PROXY: {len(cache['proxy'])} доменов → {PROXY_FILE}")
    print(f"📄 Конфиг: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
