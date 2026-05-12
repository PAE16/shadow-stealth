#!/usr/bin/env python3
"""
Генератор конфига для Shadowrocket.
На основе твоего ручного конфига.
TikTok и нейросети — всегда PROXY, российские сайты — DIRECT.
"""

import os
import re
import requests
import dns.resolver
from datetime import datetime
from typing import List, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== НАСТРОЙКИ ==========
# Ссылки на RULE-SET с доменами
RULE_SET_URLS = [
    "https://raw.githubusercontent.com/hydraponique/roscomvpn-geoip/refs/heads/release/text/direct.txt",
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/meta/geo/geoip/classical/ru.list",
    "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_community.list",
    "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_ipchecker.list",
    "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_geo_detect.list",
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
]

# Всегда DIRECT (российские критичные сервисы)
ALWAYS_DIRECT = {
    "gosuslugi.ru", "gu-st.ru", "esia.gosuslugi.ru",
    "tbank.ru", "sberbank.ru", "vtb.ru", "alfabank.ru",
    "yandex.ru", "ya.ru", "vk.com", "ok.ru", "mail.ru",
    "ozon.ru", "wildberries.ru", "avito.ru", "kinopoisk.ru",
    "vstu.ru", "volstu.ru"
}

# Всегда PROXY (TikTok, нейросети, соцсети, Google, YouTube)
ALWAYS_PROXY = {
    # TikTok
    "tiktok.com", "tiktokv.com", "tiktokcdn.com", "musical.ly", "muscdn.com",
    # Google / YouTube
    "google.com", "youtube.com", "googlevideo.com", "googleapis.com",
    "gstatic.com", "ytimg.com", "ggpht.com", "googleusercontent.com", "gmail.com",
    # Соцсети
    "instagram.com", "cdninstagram.com", "facebook.com", "fbcdn.net",
    "whatsapp.com", "whatsapp.net", "twitter.com", "twimg.com", "x.com", "threads.im",
    # Нейросети
    "openai.com", "chatgpt.com", "oaistatic.com", "oaiusercontent.com",
    "anthropic.com", "claude.ai", "gemini.google.com", "bard.google.com",
    "deepmind.google", "copilot.microsoft.com", "bing.com", "midjourney.com",
    "stability.ai", "leonardo.ai", "huggingface.co", "replicate.com",
    "runwayml.com", "perplexity.ai", "character.ai", "elevenlabs.io",
    "suno.ai", "udio.com", "grok.com", "x.ai", "poe.com", "you.com", "phind.com",
    # Другие сервисы
    "reddit.com", "discord.com", "github.com", "githubusercontent.com",
    "spotify.com", "scdn.co", "soundcloud.com", "netflix.com", "twitch.tv",
    "zoom.us", "notion.so", "cloudflare.com", "cloudfront.net"
}

TIMEOUT = 5
THREADS = 30
MAX_DOMAINS = 500

# Файлы
DIRECT_FILE = "direct.txt"
PROXY_FILE = "proxy.txt"
CONFIG_FILE = "ShadowVoice_Live.conf"

# Репозиторий (замени на свой)
REPO_BASE = "https://raw.githubusercontent.com/ТВОЙ_ЛОГИН/ТВОЙ_РЕПОЗИТОРИЙ/main"

# ========== ФУНКЦИИ ==========

def download_domains(url: str) -> Set[str]:
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return set()
        domains = set()
        for line in r.text.splitlines():
            line = line.strip()
            if not line or line.startswith(('#', ';', '//')):
                continue
            match = re.search(r'DOMAIN(?:-SUFFIX)?,([a-zA-Z0-9.-]+)', line)
            if match:
                domain = match.group(1).lower()
                if '*' not in domain and '.' in domain:
                    domains.add(domain)
        return domains
    except:
        return set()

def is_reachable(domain: str) -> bool:
    if len(domain) > 80:
        return False
    try:
        dns.resolver.resolve(domain, 'A', lifetime=TIMEOUT)
        return True
    except:
        pass
    try:
        r = requests.get(f"https://{domain}", timeout=TIMEOUT, verify=False)
        return r.status_code < 500
    except:
        return False

def check_domains(domains: List[str]) -> Tuple[List[str], List[str]]:
    direct, proxy = [], []
    print(f"\n🔍 Проверка {len(domains)} доменов...")
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        futures = {ex.submit(is_reachable, d): d for d in domains}
        for i, f in enumerate(as_completed(futures), 1):
            d = futures[f]
            if d in ALWAYS_DIRECT:
                direct.append(d)
            elif d in ALWAYS_PROXY:
                proxy.append(d)
            else:
                try:
                    if f.result():
                        direct.append(d)
                    else:
                        proxy.append(d)
                except:
                    proxy.append(d)
            if i % 100 == 0:
                print(f"  Прогресс: {i}/{len(domains)}")
    return direct, proxy

def save_rule_sets(direct: List[str], proxy: List[str]):
    with open(DIRECT_FILE, "w") as f:
        for d in sorted(set(direct)):
            f.write(f"DOMAIN-SUFFIX,{d},DIRECT\n")
    with open(PROXY_FILE, "w") as f:
        for d in sorted(set(proxy)):
            f.write(f"DOMAIN-SUFFIX,{d},PROXY\n")
    print(f"\n💾 Сохранено: DIRECT={len(direct)}, PROXY={len(proxy)}")

def generate_config():
    config = f"""#!name=ShadowVoice_Live
#!desc=Adaptive config. Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[General]
bypass-system = true
ipv6 = false
prefer-ipv6 = false
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com
tun-excluded-routes = 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.0.0.0/24, 192.0.2.0/24, 192.88.99.0/24, 192.168.0.0/16, 198.51.100.0/24, 203.0.113.0/24, 224.0.0.0/4, 255.255.255.255/32, 239.255.255.250/32
dns-server = https://cloudflare-dns.com/dns-query, system
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
DOMAIN-SUFFIX,yandexmaps.ru,DIRECT
DOMAIN-SUFFIX,maps.yandex.ru,DIRECT
DOMAIN-SUFFIX,navi.yandex.ru,DIRECT
DOMAIN,vstu.ru,DIRECT
DOMAIN,volstu.ru,DIRECT

# Mass Russian Rules (RULE-SET)
RULE-SET,{REPO_BASE}/direct.txt,DIRECT
RULE-SET,{REPO_BASE}/proxy.txt,PROXY

# Apple Services (PROXY)
IP-CIDR,17.0.0.0/8,PROXY,no-resolve
DOMAIN-SUFFIX,icloud.com,PROXY
DOMAIN-SUFFIX,icloud-content.com,PROXY
DOMAIN,api.push.apple.com,PROXY
DOMAIN-SUFFIX,apple-relay.akamaized.net,PROXY
DOMAIN-SUFFIX,apple-relay.apple.com,PROXY

# GeoIP Russia
GEOIP,RU,DIRECT

# Local networks
IP-CIDR,192.168.0.0/16,DIRECT
IP-CIDR,10.0.0.0/8,DIRECT
IP-CIDR,172.16.0.0/12,DIRECT
IP-CIDR,127.0.0.0/8,DIRECT

# Global Default
FINAL,PROXY

[Host]
localhost = 127.0.0.1

[URL Rewrite]
^http://.*$ https://$0 302

[MITM]
hostname = *yandex*, *vk*, *google*, *youtube*, *telegram*, *tiktok*, *openai*, *chatgpt*, *claude*, *midjourney*, *gemini*, *grok*
"""
    with open(CONFIG_FILE, "w") as f:
        f.write(config)
    print(f"📄 Конфиг сохранён: {CONFIG_FILE}")

def main():
    print("=" * 60)
    print("🚀 Генератор конфига Shadowrocket (на основе ручного конфига)")
    print("=" * 60)

    all_domains = set()
    print("\n📥 Скачивание списков доменов...")
    for url in RULE_SET_URLS:
        print(f"  {url.split('/')[-1]}...")
        all_domains.update(download_domains(url))
    print(f"\n📊 Всего уникальных доменов: {len(all_domains)}")

    domains_list = list(all_domains)
    if len(domains_list) > MAX_DOMAINS:
        domains_list = domains_list[:MAX_DOMAINS]
        print(f"⚠️ Для проверки взято первых {MAX_DOMAINS} доменов")

    direct, proxy = check_domains(domains_list)

    save_rule_sets(direct, proxy)
    generate_config()

    print(f"\n✅ Готово!")
    print(f"   {DIRECT_FILE} — {len(direct)} доменов (DIRECT)")
    print(f"   {PROXY_FILE} — {len(proxy)} доменов (PROXY)")
    print(f"   {CONFIG_FILE} — основной конфиг")

if __name__ == "__main__":
    main()
