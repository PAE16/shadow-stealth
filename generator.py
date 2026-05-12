import requests
import os

def main():
    # Название файла — строго такое же будет в GitHub Actions
    filename = "ShadowVoice_Live.conf"
    
    # Базовый шаблон конфига
    template = """#!name=ShadowVoice_Live
#!desc=Автоматическое обновление правил.

[General]
bypass-system = true
ipv6 = false
dns-server = https://1.1.1.2/dns-query, system
tun-excluded-routes = 10.0.0.0/8, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16

[Rule]
# --- APPLE ECOSYSTEM ---
DOMAIN,facetime.apple.com,PROXY
DOMAIN,imessage.apple.com,PROXY
DOMAIN-SUFFIX,icloud.com,PROXY

# --- STEALTH RU (Banks) ---
DOMAIN-SUFFIX,gosuslugi.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,tbank.ru,DIRECT,no-resolve
DOMAIN-SUFFIX,sberbank.ru,DIRECT,no-resolve

# --- DYNAMIC RULES ---
{DYNAMIC_RULES}

# --- FINAL ---
GEOIP,RU,DIRECT
FINAL,PROXY
"""

    # Собираем правила из внешних источников
    rules_list = []
    sources = [
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Instagram/Instagram.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/YouTube/YouTube.list"
    ]

    for url in sources:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                # Берем только строки с правилами, игнорим комменты
                valid_rules = [l for l in r.text.splitlines() if l and not l.startswith(('#', ';', '//'))]
                rules_list.extend(valid_rules)
        except:
            print(f"Не удалось загрузить: {url}")

    final_content = template.format(DYNAMIC_RULES="\n".join(rules_list))

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_content)
    
    if os.path.exists(filename):
        print(f"Успех! Файл {filename} создан. Размер: {os.path.getsize(filename)} байт.")
    else:
        print("Ошибка: Файл не был создан.")

if __name__ == "__main__":
    main()
