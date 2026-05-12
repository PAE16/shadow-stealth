#!/usr/bin/env python3
"""
Генератор адаптивного конфига Shadowrocket.
Скачивает RULE-SET с российскими И иностранными доменами,
пингует их и решает, куда отправить (DIRECT/PROXY).
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
}

# Ссылка на список рекламы
AD_SOURCE = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Advertising/Advertising_Domain.list"

# Домены, которые всегда DIRECT (даже если недоступны)
FORCE_DIRECT = {
    "gosuslugi.ru", "tbank.ru", "sberbank.ru", "vtb.ru",
    "alfabank.ru", "mail.ru", "yandex.ru", "ya.ru"
}

# Домены, которые всегда PROXY (даже если доступны)
FORCE_PROXY = {
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "youtube.com", "google.com", "gmail.com"
}

# Параметры проверки
TIMEOUT = 5          # таймаут на проверку одного домена (сек)
THREADS = 30         # количество параллельных потоков
MAX_DOMAINS = 800    # максимальное количество доменов для пинга (чтобы не слишком долго)

# Файлы
TEMPLATE_FILE = "template.conf"
OUTPUT_FILE = "ShadowVoice_Live.conf"

# ========== ФУНКЦИИ ==========

def download_list(url: str) -> List[str]:
    """Скачивает список и извлекает домены"""
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            print(f"  ⚠️ Ошибка {r.status_code} при скачивании {url}")
            return []
        content = r.text
        domains = set()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith(('#', ';', '//')):
                continue
            # Извлекаем домены из строк вида DOMAIN, domain.ru или DOMAIN-SUFFIX, domain.ru
            match = re.search(r'DOMAIN(?:-SUFFIX)?,([a-zA-Z0-9.-]+)', line)
            if match:
                domain = match.group(1).lower()
                # Фильтруем wildcard и IP-подобные
                if '*' not in domain and not re.match(r'^\d+\.\d+\.\d+\.\d+$', domain):
                    domains.add(domain)
        return list(domains)
    except Exception as e:
        print(f"  ❌ Ошибка загрузки {url}: {e}")
        return []

def is_domain_reachable(domain: str) -> bool:
    """Проверяет доступность домена (DNS + HTTPS)"""
    if len(domain) > 100 or '..' in domain:
        return False
    # DNS-проверка
    try:
        dns.resolver.resolve(domain, 'A', lifetime=TIMEOUT)
        return True
    except:
        pass
    # HTTPS-проверка
    try:
        r = requests.get(f"https://{domain}", timeout=TIMEOUT, verify=False)
        if r.status_code < 500:
            return True
    except:
        pass
    return False

def check_domains(domains: List[str]) -> Tuple[List[str], List[str]]:
    """Проверяет список доменов в многопотоке"""
    direct = []
    proxy = []
    print(f"\n🔍 Проверка {len(domains)} доменов ({THREADS} потоков, таймаут {TIMEOUT}с)...")
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        future_to_domain = {executor.submit(is_domain_reachable, d): d for d in domains}
        for i, future in enumerate(as_completed(future_to_domain), 1):
            domain = future_to_domain[future]
            try:
                reachable = future.result()
                if domain in FORCE_DIRECT:
                    direct.append(domain)
                    status = "🔒 DIRECT (forced)"
                elif domain in FORCE_PROXY:
                    proxy.append(domain)
                    status = "🔒 PROXY (forced)"
                elif reachable:
                    direct.append(domain)
                    status = "✅ DIRECT"
                else:
                    proxy.append(domain)
                    status = "❌ PROXY"
            except Exception as e:
                proxy.append(domain)
                status = f"⚠️ ERROR → PROXY"
            # Выводим каждые 50 доменов, чтобы не засорять лог
            if i % 50 == 0 or i == len(domains):
                print(f"  Прогресс: {i}/{len(domains)} доменов")
    return direct, proxy

def build_config(direct_domains: List[str], proxy_domains: List[str], ad_rules: List[str]) -> str:
    """Собирает конфиг из шаблона"""
    if not os.path.exists(TEMPLATE_FILE):
        print(f"❌ Шаблон {TEMPLATE_FILE} не найден!")
        sys.exit(1)

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    # Формируем блоки правил
    direct_block = "\n".join(f"DOMAIN-SUFFIX,{d},DIRECT" for d in sorted(set(direct_domains)))
    proxy_block = "\n".join(f"DOMAIN-SUFFIX,{d},PROXY" for d in sorted(set(proxy_domains)))
    ad_block = "\n".join(ad_rules)

    result = template.replace("{{DIRECT_DOMAINS}}", direct_block)
    result = result.replace("{{PROXY_DOMAINS}}", proxy_block)
    result = result.replace("{{AD_RULES}}", ad_block)
    result = result.replace("{{date}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return result

def main():
    print("=" * 60)
    print("🚀 Генератор адаптивного конфига Shadowrocket (русские + иностранные домены)")
    print("=" * 60)

    # 1. Скачиваем ВСЕ RULE-SET (русские и иностранные)
    all_domains = set()
    for source_type, urls in RULE_SET_URLS.items():
        print(f"\n📥 Скачиваем {source_type.upper()} RULE-SET:")
        for url in urls:
            print(f"  Загрузка {url}...")
            domains = download_list(url)
            print(f"    Найдено {len(domains)} доменов")
            all_domains.update(domains)
    print(f"\n📊 Всего уникальных доменов: {len(all_domains)}")

    # Ограничиваем количество доменов для пинга (чтобы не слишком долго)
    domains_to_check = list(all_domains)
    if len(domains_to_check) > MAX_DOMAINS:
        print(f"\n⚠️ Для пинга взято первых {MAX_DOMAINS} доменов из {len(domains_to_check)}")
        domains_to_check = domains_to_check[:MAX_DOMAINS]

    # 2. Скачиваем список рекламы
    print("\n📥 Скачиваем список рекламы...")
    ad_rules = download_list(AD_SOURCE)
    print(f"  Найдено {len(ad_rules)} рекламных доменов")

    # 3. Проверяем доступность доменов
    direct, proxy = check_domains(domains_to_check)

    # 4. Генерируем итоговый конфиг
    print("\n📝 Генерация конфига...")
    config = build_config(direct, proxy, ad_rules)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(config)

    print(f"\n✅ Конфиг сохранён в {OUTPUT_FILE}")
    print(f"📊 DIRECT: {len(direct)} доменов")
    print(f"📊 PROXY: {len(proxy)} доменов")
    print(f"📊 Реклама: {len(ad_rules)} правил")
    print(f"📄 Всего строк в конфиге: {len(config.splitlines())}")

if __name__ == "__main__":
    main()
