#!/usr/bin/env python3
"""
Автоматический генератор конфига для Shadowrocket.
Проверяет доступность российских доменов и создаёт актуальный конфиг.
"""

import os
import sys
import requests
import dns.resolver
from datetime import datetime
from typing import List, Tuple, Set

# ========== НАСТРОЙКИ ==========
# Список доменов для проверки (можно вычитывать из внешнего файла)
DEFAULT_DOMAINS = [
    "gosuslugi.ru",
    "tbank.ru",
    "sberbank.ru",
    "vtb.ru",
    "alfabank.ru",
    "magnit.ru",
    "5ka.ru",
    "perekrestok.ru",
    "ozon.ru",
    "wildberries.ru",
    "avito.ru",
    "yandex.ru",
    "vk.com",
    "ok.ru",
    "mail.ru",
    "kinopoisk.ru",
    "2gis.ru",
    "hh.ru",
    "cian.ru",
    "tutu.ru",
    "rzd.ru",
]

# Домены, которые всегда должны идти DIRECT (даже если недоступны)
FORCE_DIRECT = {"gosuslugi.ru", "tbank.ru", "sberbank.ru"}

# Домены, которые всегда должны идти PROXY (даже если доступны)
FORCE_PROXY = set()

# Файлы
DOMAINS_FILE = "domains.txt"       # можно вынести список отдельно
TEMPLATE_FILE = "template.conf"
OUTPUT_FILE = "ShadowVoice_Live.conf"

# Внешние RULE-SET (российские IP и домены)
RULE_SET_DIRECT = [
    "https://raw.githubusercontent.com/hydraponique/roscomvpn-geoip/refs/heads/release/text/direct.txt",
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/meta/geo/geoip/classical/ru.list",
]

# ========== ФУНКЦИИ ==========

def load_domains_from_file(filename: str) -> List[str]:
    """Загружает список доменов из файла (если есть)"""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return DEFAULT_DOMAINS

def is_domain_reachable(domain: str, timeout: int = 5) -> bool:
    """Проверяет доступность домена (DNS + HTTPS)"""
    # Проверяем DNS
    try:
        dns.resolver.resolve(domain, "A", lifetime=timeout)
        return True
    except:
        pass

    # Проверяем HTTPS
    try:
        r = requests.get(f"https://{domain}", timeout=timeout, verify=False)
        if r.status_code < 500:
            return True
    except:
        pass

    return False

def check_domains(domains: List[str]) -> Tuple[List[str], List[str]]:
    """Проверяет список доменов, возвращает (direct, proxy)"""
    direct = []
    proxy = []
    print("🔍 Проверка доступности доменов...")
    for domain in domains:
        if domain in FORCE_DIRECT:
            direct.append(domain)
            print(f"  🔒 {domain} → DIRECT (forced)")
        elif domain in FORCE_PROXY:
            proxy.append(domain)
            print(f"  🔒 {domain} → PROXY (forced)")
        elif is_domain_reachable(domain):
            direct.append(domain)
            print(f"  ✅ {domain} → DIRECT")
        else:
            proxy.append(domain)
            print(f"  ❌ {domain} → PROXY (blocked)")
    return direct, proxy

def generate_proxy_rules(direct_domains: List[str], proxy_domains: List[str]) -> str:
    """Генерирует секцию правил для конфига"""
    lines = []

    # DIRECT правила для российских доменов
    if direct_domains:
        lines.append("# ========== ДОМЕНЫ РФ (DIRECT) ==========")
        for d in sorted(set(direct_domains)):
            lines.append(f"DOMAIN-SUFFIX,{d},DIRECT")
        lines.append("")

    # PROXY правила для заблокированных доменов
    if proxy_domains:
        lines.append("# ========== ЗАБЛОКИРОВАННЫЕ ДОМЕНЫ (PROXY) ==========")
        for d in sorted(set(proxy_domains)):
            lines.append(f"DOMAIN-SUFFIX,{d},PROXY")
        lines.append("")

    # Базовые зарубежные сервисы (всегда PROXY)
    lines.append("# ========== ЗАРУБЕЖНЫЕ СЕРВИСЫ (PROXY) ==========")
    foreign_services = [
        "youtube.com", "googlevideo.com", "ytimg.com", "youtu.be",
        "google.com", "gmail.com", "googleapis.com",
        "instagram.com", "cdninstagram.com", "fbcdn.net",
        "facebook.com", "whatsapp.com", "whatsapp.net",
        "twitter.com", "twimg.com", "x.com",
        "t.me", "telegram.org", "tdesktop.com",
        "tiktok.com", "tiktokv.com", "tiktokcdn.com",
        "openai.com", "chatgpt.com", "oaistatic.com", "oaiusercontent.com",
        "reddit.com", "discord.com", "github.com", "spotify.com",
        "netflix.com", "twitch.tv", "zoom.us", "notion.so",
    ]
    for s in foreign_services:
        lines.append(f"DOMAIN-SUFFIX,{s},PROXY")

    return "\n".join(lines)

def generate_config(direct_domains: List[str], proxy_domains: List[str]) -> str:
    """Генерирует полный конфиг из шаблона"""
    if not os.path.exists(TEMPLATE_FILE):
        print(f"❌ Шаблон {TEMPLATE_FILE} не найден!")
        sys.exit(1)

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    proxy_rules_block = generate_proxy_rules(direct_domains, proxy_domains)

    # Вставляем всё в шаблон
    result = template.replace("{{PROXY_RULES}}", proxy_rules_block)
    result = result.replace("{{date}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return result

def main():
    print("=" * 60)
    print("🚀 Генератор конфига Shadowrocket (адаптивный к блокировкам)")
    print("=" * 60)

    # 1. Загружаем список доменов
    domains = load_domains_from_file(DOMAINS_FILE)
    print(f"📋 Загружено доменов для проверки: {len(domains)}")

    # 2. Проверяем доступность
    direct_domains, proxy_domains = check_domains(domains)

    # 3. Генерируем конфиг
    config_content = generate_config(direct_domains, proxy_domains)

    # 4. Сохраняем
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(config_content)

    print(f"\n✅ Конфиг сохранён в {OUTPUT_FILE}")
    print(f"📊 DIRECT: {len(direct_domains)} доменов")
    print(f"📊 PROXY: {len(proxy_domains)} доменов")
    print(f"📄 Размер конфига: {len(config_content.splitlines())} строк")

if __name__ == "__main__":
    main()
