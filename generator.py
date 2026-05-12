#!/usr/bin/env python3
"""
Генератор адаптивного конфига Shadowrocket.
Добавляет новые домены к существующим, не перезаписывая их.
"""

import os
import re
import json
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
TIMEOUT = 5
THREADS = 30
MAX_DOMAINS = 800

# Файлы
TEMPLATE_FILE = "template.conf"
OUTPUT_FILE = "ShadowVoice_Live.conf"
DOMAINS_CACHE_FILE = "domains_cache.json"

# ========== ФУНКЦИИ ==========

def load_cached_domains() -> Dict[str, Set[str]]:
    """Загружает кэшированные домены из файла"""
    if os.path.exists(DOMAINS_CACHE_FILE):
        with open(DOMAINS_CACHE_FILE, "r") as f:
            data = json.load(f)
            return {
                "direct": set(data.get("direct", [])),
                "proxy": set(data.get("proxy", [])),
                "ad": set(data.get("ad", [])),
            }
    return {"direct": set(), "proxy": set(), "ad": set()}

def save_cached_domains(direct: Set[str], proxy: Set[str], ad: Set[str]):
    """Сохраняет кэшированные домены в файл"""
    with open(DOMAINS_CACHE_FILE, "w") as f:
        json.dump({
            "direct": list(direct),
            "proxy": list(proxy),
            "ad": list(ad),
        }, f, indent=2)

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
            match = re.search(r'DOMAIN(?:-SUFFIX)?,([a-zA-Z0-9.-]+)', line)
            if match:
                domain = match.group(1).lower()
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
    """Проверяет список доменов в многопотоке"""
    direct = []
    proxy = []
    print(f"\n🔍 Проверка {len(domains)} доменов ({THREADS} потоков)...")
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
            if i % 100 == 0 or i == len(domains):
                print(f"  Прогресс: {i}/{len(domains)} доменов")
    return direct, proxy

def build_config(direct_domains: List[str], proxy_domains: List[str], ad_rules: List[str]) -> str:
    """Собирает конфиг из шаблона"""
    if not os.path.exists(TEMPLATE_FILE):
        print(f"❌ Шаблон {TEMPLATE_FILE} не найден!")
        sys.exit(1)

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

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
    print("🚀 Генератор адаптивного конфига Shadowrocket (с добавлением доменов)")
    print("=" * 60)

    # Загружаем кэшированные домены
    cache = load_cached_domains()
    print(f"\n📦 Загружено из кэша: DIRECT={len(cache['direct'])}, PROXY={len(cache['proxy'])}, AD={len(cache['ad'])}")

    # Скачиваем новые домены
    all_domains = set()
    for source_type, urls in RULE_SET_URLS.items():
        print(f"\n📥 Скачиваем {source_type.upper()} RULE-SET:")
        for url in urls:
            print(f"  Загрузка {url}...")
            domains = download_list(url)
            print(f"    Найдено {len(domains)} доменов")
            all_domains.update(domains)

    # Проверяем только новые домены (которых нет в кэше)
    existing_domains = cache["direct"] | cache["proxy"]
    new_domains = [d for d in all_domains if d not in existing_domains]

    print(f"\n📊 Всего уникальных доменов в источниках: {len(all_domains)}")
    print(f"📊 Из них уже есть в кэше: {len(existing_domains)}")
    print(f"📊 Новых доменов для проверки: {len(new_domains)}")

    if new_domains:
        # Проверяем только новые домены
        if len(new_domains) > MAX_DOMAINS:
            print(f"\n⚠️ Для пинга взято первых {MAX_DOMAINS} новых доменов из {len(new_domains)}")
            new_domains = new_domains[:MAX_DOMAINS]

        new_direct, new_proxy = check_domains(new_domains)

        # Добавляем новые домены к кэшу
        cache["direct"].update(new_direct)
        cache["proxy"].update(new_proxy)
    else:
        print("\n✅ Новых доменов нет, проверка не требуется")
        new_direct, new_proxy = [], []

    # Скачиваем рекламу (тоже добавляем)
    print("\n📥 Скачиваем список рекламы...")
    new_ad_rules = download_list(AD_SOURCE)
    new_ad = [r for r in new_ad_rules if r not in cache["ad"]]
    cache["ad"].update(new_ad)
    print(f"  Добавлено новых рекламных доменов: {len(new_ad)}")

    # Сохраняем кэш
    save_cached_domains(cache["direct"], cache["proxy"], cache["ad"])
    print(f"\n💾 Кэш сохранён: DIRECT={len(cache['direct'])}, PROXY={len(cache['proxy'])}, AD={len(cache['ad'])}")

    # Генерируем конфиг
    print("\n📝 Генерация конфига...")
    config = build_config(list(cache["direct"]), list(cache["proxy"]), list(cache["ad"]))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(config)

    print(f"\n✅ Конфиг сохранён в {OUTPUT_FILE}")
    print(f"📊 Итого в конфиге: DIRECT={len(cache['direct'])}, PROXY={len(cache['proxy'])}, AD={len(cache['ad'])}")
    print(f"📄 Всего строк: {len(config.splitlines())}")

if __name__ == "__main__":
    main()