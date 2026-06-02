import os
import requests
from datetime import datetime

# ========== ТВОИ DoH-ССЫЛКИ (ЕВРОПА) ==========
DNS_CUSTOM_URL = "https://nl.e0f.bz/dns-query/u-3709255d"  # Нидерланды
DNS_BACKUP_URL = "https://de.e0f.bz/dns-query/u-3709255d"  # Германия
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
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Instagram/Instagram.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/TikTok/TikTok.list"
    ],
    "direct": [
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_yandex.list",
        "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_vk.list"
    ]
}

def clean_rule_line(line):
    """Очищает строку от префиксов Shadowrocket, оставляя только чистый домен или IP."""
    line = line.strip()
    if not line or line.startswith("#") or line.startswith(";"):
        return None
    
    # Удаляем служебные префиксы, если они уже есть в файлах
    for prefix in ["DOMAIN-SUFFIX,", "DOMAIN,", "DOMAIN-KEYWORD,", "IP-CIDR,", "IP-ASN,"]:
        if line.startswith(prefix):
            line = line.replace(prefix, "")
            break
            
    # Отрезаем суффиксы политик (,PROXY или ,DIRECT), если они прилетели из файлов
    if ",PROXY" in line:
        line = line.split(",PROXY")[0]
    if ",DIRECT" in line:
        line = line.split(",DIRECT")[0]
    if ",no-resolve" in line:
        line = line.split(",no-resolve")[0]
        
    return line.strip()

def load_local_rules(file_path):
    """Загружает существующие правила из репозитория (режим накопления)."""
    if not os.path.exists(file_path):
        return set()
    rules = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            cleaned = clean_rule_line(line)
            if cleaned:
                rules.add(cleaned)
    return rules

def fetch_remote_rules(urls):
    """Скачивает свежие правила из сети."""
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
            print(f"⚠️ Ошибка скачивания источника {url}: {e}")
    return rules

def save_list_file(file_path, rules_set, policy_type):
    """Сохраняет накопленные правила в чистом, красивом формате для репозитория."""
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
    print("🔄 Запуск генератора в режиме строгого синтаксиса...")

    # Читаем старую накопленную базу
    existing_proxy = load_local_rules(PROXY_FILE)
    existing_direct = load_local_rules(DIRECT_FILE)

    # Качаем обновы
    remote_proxy = fetch_remote_rules(RULE_SOURCES["proxy"])
    remote_direct = fetch_remote_rules(RULE_SOURCES["direct"])

    # Объединяем (накопление)
    full_proxy = existing_proxy.union(remote_proxy)
    full_direct = existing_direct.union(remote_direct)

    # Убираем пересечения
    full_proxy = full_proxy - full_direct
    
    # Принудительно вычищаем ключевые слова соцсетей из общего списка, так как они вшиты в топ конфига
    for service_word in ["telegram", "tiktok", "instagram", "t.me", "tiktokv.com", "orgeo.ru"]:
        full_proxy.discard(service_word)
        full_direct.discard(service_word)

    # Сохраняем текстовые списки обратно в репозиторий
    save_list_file(PROXY_FILE, full_proxy, "PROXY")
    save_list_file(DIRECT_FILE, full_direct, "DIRECT")

    # Сборка финального шаблона .conf
    dns_line = f"dns-server = {DNS_CUSTOM_URL}, {DNS_BACKUP_URL}, {DNS_PUBLIC}"
    
    config_template = f"""#!name=ShadowVoice_Live
#!desc=Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Накопительный режим | NaiveProxy & Amnezia Сompatible

[General]
bypass-system = true
ipv6 = false
prefer-ipv6 = false
{dns_line}
dns-direct-system = true
dns-direct-received = true
tun-excluded-routes = 10.0.0.0/8, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 100.64.0.0/10
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com

[Rule]
# --- КРИТИЧЕСКИЙ ПРИОРИТЕТ ДЛЯ СЛОЖНЫХ ПРОТОКОЛОВ (ТТ и ТГ) ---
DOMAIN-KEYWORD,telegram,PROXY
DOMAIN-KEYWORD,tiktok,PROXY
DOMAIN-SUFFIX,t.me,PROXY
DOMAIN-SUFFIX,tiktokv.com,PROXY

# --- СТАБИЛИЗАЦИЯ ТУННЕЛЯ (БЛОК QUIC) ---
AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP

# --- СТРОГИЙ DIRECT ДЛЯ РФ-СЕРВИСОВ ---
DOMAIN-SUFFIX,gosuslugi.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,tbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,sberbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,orgeo.ru,DIRECT,no-resolve

# --- НАКОПЛЕННЫЙ СПИСОК DIRECT ---
"""

    # Записываем блок DIRECT
    for rule in sorted(list(full_direct)):
        if "/" in rule:
            config_template += f"IP-CIDR,{rule},DIRECT,no-resolve\n"
        elif rule.isdigit():
            config_template += f"IP-ASN,{rule},DIRECT,no-resolve\n"
        elif rule.count(".") >= 1:
            config_template += f"DOMAIN-SUFFIX,{rule},DIRECT\n"
        else:
            config_template += f"DOMAIN-KEYWORD,{rule},DIRECT\n"

    config_template += "\n# --- НАКОПЛЕННЫЙ СПИСОК PROXY ---\n"

    # Записываем блок PROXY
    for rule in sorted(list(full_proxy)):
        if "/" in rule:
            config_template += f"IP-CIDR,{rule},PROXY,no-resolve\n"
        elif rule.isdigit():
            config_template += f"IP-ASN,{rule},PROXY,no-resolve\n"
        elif rule.count(".") >= 1:
            config_template += f"DOMAIN-SUFFIX,{rule},PROXY\n"
        else:
            config_template += f"DOMAIN-KEYWORD,{rule},PROXY\n"

    # Закрывающая заглушка
    config_template += """
# --- ПОСТ-ФИЛЬТРАЦИЯ ---
DOMAIN-SUFFIX,ru,DIRECT,no-resolve
GEOIP,RU,DIRECT
FINAL,PROXY
"""

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(config_template.strip() + "\n")
        
    print(f"📊 Сборка завершена успешно! Записано правил в конфиг: DIRECT={len(full_direct)}, PROXY={len(full_proxy)}")

if __name__ == "__main__":
    main()
