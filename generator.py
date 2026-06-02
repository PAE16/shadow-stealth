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

def load_local_rules(file_path):
    """Загружает существующие правила из файла, чтобы не затереть ручные правки."""
    if not os.path.exists(file_path):
        return set()
    rules = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                rules.add(line)
    return rules

def fetch_remote_rules(urls):
    """Скачивает списки правил из удаленных репозиториев."""
    rules = set()
    for url in urls:
        try:
            response = requests.get(url, timeout=15)
            if response.status_with == 200:
                for line in response.text.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith(";"):
                        # Приводим к единому формату для Shadowrocket
                        rules.add(line)
        except Exception as e:
            print(f"⚠️ Ошибка при скачивании {url}: {e}")
    return rules

def save_list_file(file_path, rules_set):
    """Сохраняет отсортированный список правил в файл."""
    with open(file_path, "w", encoding="utf-8") as f:
        for rule in sorted(list(rules_set)):
            f.write(f"{rule}\n")

def main():
    print("🔄 Запуск накопления и генерации конфигурации...")

    # Шаг 1. Читаем то, что УЖЕ есть в репозитории (твоя ручная база)
    existing_proxy = load_local_rules(PROXY_FILE)
    existing_direct = load_local_rules(DIRECT_FILE)

    print(f"📊 База до запуска: Накоплено PROXY: {len(existing_proxy)}, DIRECT: {len(existing_direct)}")

    # Шаг 2. Скачиваем свежие обновления из интернета
    remote_proxy = fetch_remote_rules(RULE_SOURCES["proxy"])
    remote_direct = fetch_remote_rules(RULE_SOURCES["direct"])

    # Шаг 3. Объединяем старое и новое (Режим НАКОПЛЕНИЯ)
    full_proxy = existing_proxy.union(remote_proxy)
    full_direct = existing_direct.union(remote_direct)

    # Принудительная очистка пересечений (если домен есть в direct, убираем из proxy)
    full_proxy = full_proxy - full_direct

    # Шаг 4. Сохраняем обновленные текстовые файлы (они теперь будут только расти)
    save_list_file(PROXY_FILE, full_proxy)
    save_list_file(DIRECT_FILE, full_direct)
    print(f"💾 Списки обновлены! Итого в базе: PROXY: {len(full_proxy)}, DIRECT: {len(full_direct)}")

    # Шаг 5. Сборка финального файла конфигурации .conf
    dns_line = f"dns-server = {DNS_CUSTOM_URL}, {DNS_BACKUP_URL}, {DNS_PUBLIC}"

    # Настройки совместимости под современные защищенные протоколы (AmneziaWG, NaiveProxy)
    config_template = f"""#!name=ShadowVoice_Live
#!desc=Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Накопительный режим | Multi-Protocol Fix

[General]
bypass-system = true
ipv6 = false
prefer-ipv6 = false
{dns_line}
dns-direct-system = true
dns-direct-received = true
# Исключения для локальных сетей (чтобы не отваливалась раздача и домашнее окружение)
tun-excluded-routes = 10.0.0.0/8, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 100.64.0.0/10
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com

[Rule]
# --- КРИТИЧЕСКИЙ ПРИОРИТЕТ (Фиксы ТТ и ТГ) ---
DOMAIN-KEYWORD,telegram,PROXY
DOMAIN-KEYWORD,tiktok,PROXY
DOMAIN-SUFFIX,t.me,PROXY
DOMAIN-SUFFIX,tiktokv.com,PROXY

# --- БЛОКИРОВКА QUIC ДЛЯ СТАБИЛЬНОСТИ AMNEZIAWG/NAIVE ---
AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP

# --- СТРОГИЙ DIRECT И ФИКСЫ РЕГИОНАЛЬНЫХ ОШИБОК МАРШРУТИЗАЦИИ ---
DOMAIN-SUFFIX,gosuslugi.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,tbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,sberbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,orgeo.ru,DIRECT,no-resolve

# --- НАКОПЛЕННЫЙ СПИСОК DIRECT ---
"""
    
    # Добавляем все директ правила
    for rule in sorted(list(full_direct)):
        if not rule.startswith("DOMAIN") and not rule.startswith("IP-"):
            # Если в списке просто домен, оборачиваем в стандартный формат
            config_template += f"DOMAIN-SUFFIX,{rule},DIRECT\n"
        else:
            config_template += f"{rule},DIRECT\n"

    config_template += "\n# --- НАКОПЛЕННЫЙ СПИСОК PROXY ---\n"
    
    # Добавляем все прокси правила
    for rule in sorted(list(full_proxy)):
        if not rule.startswith("DOMAIN") and not rule.startswith("IP-"):
            config_template += f"DOMAIN-SUFFIX,{rule},PROXY\n"
        else:
            config_template += f"{rule},PROXY\n"

    # Финальные правила-заглушки
    config_template += """
# --- ПОСТ-ФИЛЬТРАЦИЯ И ГЕО-ПРАВИЛА ---
DOMAIN-SUFFIX,ru,DIRECT,no-resolve
GEOIP,RU,DIRECT
FINAL,PROXY
"""

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(config_template.strip() + "\n")
        
    print("✅ Конфигурационный файл ShadowVoice_Live.conf успешно собран!")

if __name__ == "__main__":
    main()
