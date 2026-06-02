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

# Полный список апстримов для обновления и глубокого накопления
RULE_SOURCES = {
    "proxy": [
        f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/proxy.txt", # Твоя база
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/ai.list",       # НОВОЕ
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/fitness.list",  # НОВОЕ
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/games.list",    # НОВОЕ
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/main.list",     # НОВОЕ
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/meta.list",     # НОВОЕ
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/telegram.list", # НОВОЕ
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_community.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_ipchecker.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_geo_detect.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Telegram/Telegram.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Instagram/Instagram.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/TikTok/TikTok.list"
    ],
    "direct": [
        f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/direct.txt", # Твоя база
        "https://raw.githubusercontent.com/tatarinovms/ShadowRocketSimpleConfig/refs/heads/main/lists/rudirect.list", # НОВОЕ
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_yandex.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_vk.list"
    ]
}

def clean_rule_line(line):
    """Очищает входящие строки от мусора и префиксов, оставляя чистое правило."""
    line = line.strip()
    if not line or line.startswith("#") or line.startswith(";"):
        return None
    
    # Срезаем служебные типы правил Shadowrocket
    for prefix in ["DOMAIN-SUFFIX,", "DOMAIN,", "DOMAIN-KEYWORD,", "IP-CIDR,", "IP-ASN,"]:
        if line.startswith(prefix):
            line = line.replace(prefix, "")
            break
            
    # Удаляем привязанные политики маршрутизации
    if ",PROXY" in line: line = line.split(",PROXY")[0]
    if ",DIRECT" in line: line = line.split(",DIRECT")[0]
    if ",no-resolve" in line: line = line.split(",no-resolve")[0]
        
    return line.strip()

def fetch_rules(urls):
    """Скачивает правила из переданного списка URL и очищает их."""
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
            print(f"⚠️ Временный пропуск апстрима (таймаут или ошибка): {url}")
    return rules

def save_list_file(file_path, rules_set):
    """Форматирует правила под синтаксис Shadowrocket и сохраняет их в файлы накопления."""
    with open(file_path, "w", encoding="utf-8") as f:
        for rule in sorted(list(rules_set)):
            if rule.count(".") >= 1 and not rule.replace(".", "").isdigit():
                f.write(f"DOMAIN-SUFFIX,{rule}\n")
            elif "/" in rule:
                f.write(f"IP-CIDR,{rule},no-resolve\n")
            elif rule.isdigit():
                f.write(f"IP-ASN,{rule},no-resolve\n")
            else:
                f.write(f"DOMAIN-KEYWORD,{rule}\n")

def main():
    print(f"🔄 Старт инкрементального накопительного генератора для {GITHUB_USERNAME}...")

    # Шаг 1. Парсим и объединяем абсолютно все правила (из твоих файлов и из внешних источников)
    print("📥 Сбор доменов из твоих баз и внешних апстримов...")
    full_proxy = fetch_rules(RULE_SOURCES["proxy"])
    full_direct = fetch_rules(RULE_SOURCES["direct"])

    # Шаг 2. Исключаем пересечения (DIRECT приоритетнее)
    full_proxy = full_proxy - full_direct
    
    # Исключаем жестко зашитые в шапку критические сервисы
    for service_word in ["telegram", "tiktok", "instagram", "t.me", "tiktokv.com", "orgeo.ru"]:
        full_proxy.discard(service_word)
        full_direct.discard(service_word)

    # Шаг 3. Сохраняем обновленные, расширенные базы в файлы репозитория
    save_list_file(PROXY_FILE, full_proxy)
    save_list_file(DIRECT_FILE, full_direct)
    print(f"💾 Накопительные списки расширены! Итого в базе: DIRECT={len(full_direct)}, PROXY={len(full_proxy)}")

    # Шаг 4. Настраиваем ссылки RULE-SET на твои обновленные списки
    raw_url_direct = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/direct.txt"
    raw_url_proxy = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/proxy.txt"

    dns_line = f"dns-server = {DNS_CUSTOM_URL}, {DNS_BACKUP_URL}, {DNS_PUBLIC}"
    
    # Шаг 5. Сборка легкого файла конфигурации ShadowVoice_Live.conf
    config_template = f"""# Generated by shadowrocket-config-generator | {datetime.now().strftime('%a, %d %b %Y %H:%M:%S')} GMT
# РЕЖИМ: УЛЬТРА-ЛЕГКИЙ КОНФИГ С ВНЕШНИМИ НАБОРАМИ ПРАВИЛ
# Оптимизация: NaiveProxy, AmneziaWG, Домашняя сеть и Режим модема iOS

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
# --- КРИТИЧЕСКИЙ ПРИОРИТЕТ ДЛЯ СЛОЖНЫХ ПРОТОКОЛОВ (ТТ и ТГ) ---
DOMAIN-KEYWORD,telegram,PROXY
DOMAIN-KEYWORD,tiktok,PROXY
DOMAIN-SUFFIX,t.me,PROXY
DOMAIN-SUFFIX,tiktokv.com,PROXY

# --- СТАБИЛИЗАЦИЯ ТУННЕЛЯ (БЛОК QUIC ДЛЯ NAIVE/AMNEZIA) ---
AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP

# --- ЖЕСТКИЙ DIRECT ДЛЯ РФ-СЕРВИСОВ И ОРГЕО ---
DOMAIN-SUFFIX,gosuslugi.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,tbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,sberbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,orgeo.ru,DIRECT,no-resolve

# --- ВНЕШНИЕ НАКОПИТЕЛЬНЫЕ НАБОРЫ ПРАВИЛ (RULE-SET) ---
RULE-SET,{raw_url_direct},DIRECT
RULE-SET,{raw_url_proxy},PROXY

# --- ПОСТ-ФИЛЬТРАЦИЯ ---
DOMAIN-SUFFIX,ru,DIRECT,no-resolve
GEOIP,RU,DIRECT
FINAL,PROXY
"""

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(config_template.strip() + "\n")
        
    print(f"🚀 Сборка завершена! Легкий конфиг {CONFIG_FILE} успешно обновлен.")

if __name__ == "__main__":
    main()
