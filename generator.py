import requests

def get_external_rules():
    # Загружаем проверенный Rule-Set (например, от комьюнити)
    # Здесь можно добавить любые внешние ссылки на списки доменов
    sources = [
        "https://raw.githubusercontent.com/yebekhe/Telegram-V2ray-Config/main/rules/openai.txt",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Instagram/Instagram.list"
    ]
    
    collected_rules = []
    for url in sources:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                # Фильтруем пустые строки и комментарии
                lines = [l for l in resp.text.splitlines() if l and not l.startswith("#")]
                collected_rules.extend(lines)
        except:
            continue
    return "\n".join(collected_rules)

def main():
    with open("template.conf", "r", encoding="utf-8") as f:
        content = f.read()
    
    dynamic_rules = get_external_rules()
    
    # Вставляем динамические правила в место заполнителя
    final_conf = content.replace("# {DYNAMIC_RULES_PLACEHOLDER}", dynamic_rules)
    
    with open("S010lvloon_Live.conf", "w", encoding="utf-8") as f:
        f.write(final_conf)

if __name__ == "__main__":
    main()
