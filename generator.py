import os
import requests
from datetime import datetime

# Названия файлов
CONFIG_FILE = "ShadowVoice_Live.conf"
DIRECT_FILE = "direct.txt"
PROXY_FILE = "proxy.txt"

# Источники правил
RULE_SOURCES = {
    "proxy": [
        # Твои новые списки
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_community.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_ipchecker.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_geo_detect.list",
        # Основные сервисы
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Telegram/Telegram.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/TikTok/TikTok.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/YouTube/YouTube.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Instagram/Instagram.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/OpenAI/OpenAI.list"
    ],
    "direct": [
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Yandex/Yandex.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/VK/VK.list"
    ]
}

def download_rules(urls):
    rules = set()
    for url in urls:
        try:
            # Преобразуем ссылки на github в raw, если они в обычном формате
            raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            r = requests.get(raw_url, timeout=15)
            if r.status_code == 200:
                lines = [l.strip() for l in r.text.splitlines() if l.strip() and not l.startswith(('#', ';'))]
                rules.update(lines)
        except: print(f"⚠️ Ошибка загрузки: {url}")
    return sorted(list(rules))

def main():
    print("🚀 Запуск генератора (Ultra Pack: Community + IPCheckers)...")
    
    proxy_rules = download_rules(RULE_SOURCES["proxy"])
    direct_rules = download_rules(RULE_SOURCES["direct"])

    with open(DIRECT_FILE, "w") as f: f.write("\n".join(direct_rules))
    with open(PROXY_FILE, "w") as f: f.write("\n".join(proxy_rules))

    config_template = f"""#!name=ShadowVoice_Live
#!desc=Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Community & IPCheckers Fix

[General]
bypass-system = true
ipv6 = false
prefer-ipv6 = false
dns-server = https://1.1.1.1/dns-query, https://dns.google/dns-query, system
dns-direct-system = true
tun-excluded-routes = 10.0.0.0/8, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 100.64.0.0/10
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com

[Rule]
# --- TELEGRAM & TIKTOK (Priority Fix) ---
DOMAIN-KEYWORD,telegram,PROXY
DOMAIN-KEYWORD,tiktok,PROXY
DOMAIN-SUFFIX,t.me,PROXY
DOMAIN-SUFFIX,tiktokv.com,PROXY

# --- BLOCK QUIC ---
AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP

# --- SYSTEM & BANKS (Strict Direct) ---
DOMAIN-SUFFIX,gosuslugi.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,tbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,sberbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,vtb.ru,DIRECT,no-resolve

# --- DYNAMIC RULES (Community + IP Checkers) ---
{chr(10).join([r for r in proxy_rules if "telegram" not in r.lower() and "tiktok" not in r.lower()])}

# --- FINAL ---
DOMAIN-SUFFIX,ru,DIRECT,no-resolve
GEOIP,RU,DIRECT
FINAL,PROXY
"""

    with open(CONFIG_FILE, "w") as f:
        f.write(config_template)
    print(f"✅ Конфиг успешно собран с учетом новых списков!")

if __name__ == "__main__":
    main()
