import os
import requests
from datetime import datetime

# ==================== НАСТРОЙКА РЕПОЗИТОРИЯ ====================
GITHUB_USERNAME = "PAE16"
GITHUB_REPO = "shadow-stealth"
# ===============================================================

# ========== ТВОИ DoH-ССЫЛКИ (ЕВРОПА) ==========
DNS_CUSTOM_URL = "https://nl.e0f.bz/dns-query/u-3709255d"  # Нидерланды
DNS_BACKUP_URL = "https://de.e0f.bz/dns-query/u-3709255d"  # Германия
DNS_PUBLIC = "https://1.1.1.1/dns-query, https://dns.google/dns-query, system"
# ============================================

CONFIG_FILE = "ShadowVoice_Live.conf"
DIRECT_FILE = "direct.txt"
PROXY_FILE = "proxy.txt"

# Источники для накопления
RULE_SOURCES = {
    "proxy": [
        f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/proxy.txt",
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/ai.list",
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/fitness.list",
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/games.list",
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/main.list",
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/meta.list",
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/telegram.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_community.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_ipchecker.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_geo_detect.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Telegram/Telegram.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Instagram/Instagram.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/TikTok/TikTok.list"
    ],
    "direct": [
        f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/direct.txt",
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/rudirect.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_yandex.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_vk.list"
    ]
}

def clean_rule_line(line):
    line = line.strip()
    if not line or line.startswith("#") or line.startswith(";"):
        return None
    
    is_ip_cidr = "IP-CIDR" in line or "/" in line
    is_ip_asn = "IP-ASN" in line
    
    for prefix in ["DOMAIN-SUFFIX,", "DOMAIN,", "DOMAIN-KEYWORD,", "IP-CIDR,", "IP-ASN,"]:
        if line.startswith(prefix):
            line = line.replace(prefix, "")
            break
            
    if ",PROXY" in line: line = line.split(",PROXY")[0]
    if ",DIRECT" in line: line = line.split(",DIRECT")[0]
    if ",no-resolve" in line: line = line.split(",no-resolve")[0]
    
    cleaned = line.strip()
    if not cleaned:
        return None
        
    if is_ip_cidr:
        return f"IP-CIDR,{cleaned},no-resolve"
    elif is_ip_asn:
        return f"IP-ASN,{cleaned},no-resolve"
    else:
        return cleaned

def fetch_rules(urls):
    rules = set()
    for url in urls:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                for line in response.text.splitlines():
                    cleaned = clean_rule_line(line)
                    if cleaned:
                        rules.add(cleaned)
        except Exception as e:
            print(f"⚠️ Пропущен источник: {url}")
    return rules

def save_clean_file(file_path, rules_set):
    with open(file_path, "w", encoding="utf-8") as f:
        for rule in sorted(list(rules_set)):
            f.write(f"{rule}\n")

def main():
    print(f"🔄 Запуск генератора с фиксом рекомендаций ТТ для {GITHUB_USERNAME}...")

    full_proxy = fetch_rules(RULE_SOURCES["proxy"])
    full_direct = fetch_rules(RULE_SOURCES["direct"])

    full_proxy = full_proxy - full_direct
    
    for service in ["telegram", "tiktok", "instagram", "t.me", "tiktokv.com", "orgeo.ru"]:
        full_proxy.discard(service)
        full_direct.discard(service)

    save_clean_file(PROXY_FILE, full_proxy)
    save_clean_file(DIRECT_FILE, full_direct)

    raw_url_direct = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/direct.txt"
    raw_url_proxy = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/proxy.txt"

    dns_line = f"dns-server = {DNS_CUSTOM_URL}, {DNS_BACKUP_URL}, {DNS_PUBLIC}"
    
    # Шаблон .conf файла с глубоким спуфингом ТТ (Подменяем на регион US - США)
    config_template = f"""# Generated by shadowrocket-config-generator | {datetime.now().strftime('%a, %d %b %Y %H:%M:%S')} GMT
# Оптимизация: Фикс разрывов + Смена региона TikTok на США (US)

[General]
bypass-system = true
ipv6 = false
prefer-ipv6 = false
private-ip-answer = true
{dns_line}
dns-direct-system = true
dns-direct-received = true
dns-fallback-system = true
dns-direct-fallback-proxy = true
fallback-dns-server = tls://77.88.8.88:853,https://safe.dot.dns.yandex.net/dns-query,77.88.8.88,system
hijack-dns = :53
skip-proxy = 192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,localhost,*.local,captive.apple.com
tun-excluded-routes = 10.0.0.0/8,100.64.0.0/10,127.0.0.0/8,169.254.0.0/16,172.16.0.0/12,192.0.0.0/24,192.0.2.0/24,192.88.99.0/24,192.168.0.0/16,198.51.100.0/24,203.0.113.0/24,224.0.0.0/4,255.255.255.255/32,239.255.255.250/32
icmp-auto-reply = false
always-reject-url-rewrite = false
udp-policy-not-supported-behaviour = REJECT

[Rule]
# --- ЖЕСТКИЙ ПРИОРИТЕТ ДЛЯ МЕДИА ---
DOMAIN-KEYWORD,telegram,PROXY
DOMAIN-KEYWORD,tiktok,PROXY
DOMAIN-SUFFIX,t.me,PROXY
DOMAIN-SUFFIX,tiktokv.com,PROXY

# --- БЛОКИРОВКА QUIC (Перевод ТТ на TCP) ---
AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP

# --- СТРОГИЙ DIRECT ---
DOMAIN-SUFFIX,gosuslugi.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,tbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,sberbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,orgeo.ru,DIRECT,no-resolve

# --- НАКОПИТЕЛЬНЫЕ НАБОРЫ (RULE-SET) ---
RULE-SET,{raw_url_direct},DIRECT
RULE-SET,{raw_url_proxy},PROXY

DOMAIN-SUFFIX,ru,DIRECT,no-resolve
GEOIP,RU,DIRECT
FINAL,PROXY

https://monica.im/en/tools/rewrite-text
# Смена региона TikTok. На лету подменяет системные заголовки кодов SIM-карт на США (можешь заменить US на UK или DE)
(?<=_region=)CN(?=&) US 307
(?<=&mcc_mnc=)460[0-9]{{2}}(?=&) 310260 307
(^https?://\\w+-tiktok\\.amemv\\.com/opt/v1/list.+) REJECT
(^https?://\\w+\\.tiktokv\\.com/aweme/v1/feed.+) header_replace "X-Tt-Token" ""

[MITM]
# Включаем расшифровку HTTPS для доменов ТТ, чтобы инжектить подмену региона
hostname = *.tiktokv.com, *.byteoversea.com, *.tik-tokapi.com
"""

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(config_template.strip() + "\n")
        
    print(f"🚀 Сборка завершена! Конфиг {CONFIG_FILE} пропатчен на регион US.")

if __name__ == "__main__":
    main()
