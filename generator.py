import os
import requests
from datetime import datetime

# ========== ТВОИ DoH-ССЫЛКИ (ЕВРОПА) ==========
# Первая в списке будет использоваться по умолчанию
DNS_CUSTOM_URL = "https://nl.e0f.bz/dns-query/u-3709255d"  # Нидерланды
# Резервная DoH-ссылка (Германия), если первая недоступна
DNS_BACKUP_URL = "https://de.e0f.bz/dns-query/u-3709255d"
# Стандартные публичные DNS (запасные)
DNS_PUBLIC = "https://1.1.1.1/dns-query, https://dns.google/dns-query, system"
# ============================================

CONFIG_FILE = "ShadowVoice_Live.conf"
DIRECT_FILE = "direct.txt"
PROXY_FILE = "proxy.txt"

RULE_SOURCES = {
    "proxy": [
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_community.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_ipchecker.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_geo_detect.list",
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
            raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            r = requests.get(raw_url, timeout=15)
            if r.status_code == 200:
                lines = [l.strip() for l in r.text.splitlines() if l.strip() and not l.startswith(('#', ';'))]
                rules.update(lines)
        except:
            print(f"⚠️ Ошибка загрузки: {url}")
    return sorted(list(rules))

def main():
    print("🚀 Запуск генератора с твоими DoH-серверами...")

    proxy_rules = download_rules(RULE_SOURCES["proxy"])
    direct_rules = download_rules(RULE_SOURCES["direct"])

    with open(DIRECT_FILE, "w") as f:
        f.write("\n".join(direct_rules))
    with open(PROXY_FILE, "w") as f:
        f.write("\n".join(proxy_rules))

    # Формируем строку DNS: твоя ссылка (основная) + резервная + публичные
    dns_line = f"dns-server = {DNS_CUSTOM_URL}, {DNS_BACKUP_URL}, {DNS_PUBLIC}"

    config_template = f"""#!name=ShadowVoice_Live
#!desc=Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Community & IPCheckers Fix

[General]
bypass-system = true
ipv6 = false
prefer-ipv6 = false
{dns_line}
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

    print(f"✅ Конфиг успешно собран!")
    print(f"📍 Основной DoH: {DNS_CUSTOM_URL}")
    print(f"📍 Резервный DoH: {DNS_BACKUP_URL}")
    print(f"📍 Резервные DNS: {DNS_PUBLIC}")

if __name__ == "__main__":
    main()
