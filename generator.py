import requests

def main():
    # Твой шаблон
    template = """[General]
bypass-system = true
[Rule]
# {DYNAMIC_RULES}
FINAL,PROXY"""

    # Пример получения правил (можешь заменить на свои ссылки)
    try:
        # Для теста добавим хотя бы одно правило, чтобы файл не был пустым
        dynamic_rules = "DOMAIN-SUFFIX,google.com,PROXY\nDOMAIN-SUFFIX,instagram.com,PROXY"
    except:
        dynamic_rules = ""

    final_conf = template.replace("# {DYNAMIC_RULES}", dynamic_rules)

    # ВАЖНО: Имя файла должно быть ShadowVoice_Live.conf
    with open("ShadowVoice_Live.conf", "w", encoding="utf-8") as f:
        f.write(final_conf)
    print("Файл ShadowVoice_Live.conf успешно создан.")

if __name__ == "__main__":
    main()
