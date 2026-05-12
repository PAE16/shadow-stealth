import requests
import os

def main():
    filename = "ShadowVoice_Live.conf"
    
    # 1. Загружаем внешние списки правил (Proxy)
    proxy_sources = {
        "YouTube": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/YouTube/YouTube.list",
        "Instagram": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Instagram/Instagram.list",
        "OpenAI": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/OpenAI/OpenAI.list",
        "TikTok": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/TikTok/TikTok.list",
        "Twitter": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Twitter/Twitter.list"
    }

    # 2. Загружаем список рекламы (Reject)
    ad_source = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Advertising/Advertising_Domain.list"

    dynamic_proxy_rules = []
    dynamic_reject_rules = []

    print("Начинаю сбор правил...")

    # Собираем прокси-правила
    for name, url in proxy_sources.items():
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                rules = [l for l in r.text.splitlines() if l and not l.startswith(('#', ';', '//'))]
                # Форсируем использование PROXY для этих правил
                formatted = [l.replace("DIRECT", "PROXY").replace("REJECT", "PROXY") for l in rules]
                dynamic_proxy_rules.extend(formatted)
                print(f"✅ {name}: добавлено {len(rules)} строк")
        except:
            print(f"❌ Ошибка загрузки {name}")

    # Собираем рекламу
    try:
        r = requests.get(ad_source, timeout=10)
        if r.status_code == 200:
            rules = [l for l in r.text.splitlines() if l and not l.startswith(('#', ';', '//'))]
            dynamic_reject_rules.extend(rules)
            print(f"✅ Реклама: добавлено {len(rules)} строк")
    except:
        print("❌ Ошибка загрузки списка рекламы")

    # 3. Формируем итоговый конфиг
    template = f"""#!name=ShadowVoice_Live
#!desc=Stealth Config by AkiCode. Последнее обновление: {{date}}

[General]
bypass-system = true
ipv6 = false
prefer-ipv6 = false
dns-server = https://1.1.1.2/dns-query, system
dns-direct-system = true
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com
tun-excluded-routes = 10.0.0.0/8, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 100.64.0.0/10

[Rule]
# --- СЕКЦИЯ 1: РЕКЛАМА (REJECT) ---
{chr(10).join(dynamic_reject_rules)}

# --- СЕКЦИЯ 2: APPLE & SYSTEM ---
DOMAIN,facetime.apple.com,PROXY
DOMAIN,imessage.apple.com,PROXY
DOMAIN-SUFFIX,icloud.com,PROXY
DOMAIN-SUFFIX,apple-cloudkit.com,PROXY

# --- СЕКЦИЯ 3: STEALTH RU (Банки и Госуслуги - строго DIRECT + no-resolve) ---
DOMAIN-SUFFIX,gosuslugi.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,tbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,tinkoff.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,sberbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,vtb.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,alfabank.ru,DIRECT,no-resolve

# --- СЕКЦИЯ 4: ДИНАМИЧЕСКИЕ ПРОКСИ ---
{chr(10).join(dynamic_proxy_rules)}

# --- СЕКЦИЯ 5: ФИНАЛЬНЫЙ WHITELIST ---
DOMAIN-SUFFIX,ru,DIRECT,no-resolve
GEOIP,RU,DIRECT
FINAL,PROXY
"""
    
    from datetime import datetime
    final_content = template.replace("{date}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_content)
    
    print(f"Финиш! Файл {filename} готов.")

if __name__ == "__main__":
    main()
