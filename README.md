# ShadowVoice Live — адаптивный конфиг для Shadowrocket

[![Generate Config](https://github.com/ТВОЙ_ЛОГИН/ТВОЙ_РЕПОЗИТОРИЙ/actions/workflows/main.yml/badge.svg)](https://github.com/ТВОЙ_ЛОГИН/ТВОЙ_РЕПОЗИТОРИЙ/actions/workflows/main.yml)

**Автоматический генератор конфига для Shadowrocket.**  
Скрипт сам проверяет доступность сайтов и решает, какой трафик отправлять через VPN (PROXY), а какой напрямую (DIRECT).

## 🔄 Как это работает

1. **GitHub Actions** запускается **каждый час**
2. Скрипт `generator.py` скачивает актуальные списки доменов:
   - Российские сайты (банки, госуслуги, соцсети)
   - Иностранные сервисы (Google, YouTube, Instagram, TikTok, Telegram и др.)
   - Рекламные домены
3. Каждый домен **пингуется** (DNS + HTTPS)
4. Доступные сайты идут в **DIRECT**, недоступные — в **PROXY**
5. Готовый конфиг `ShadowVoice_Live.conf` сохраняется в репозиторий

## 📲 Установка в Shadowrocket

1. Скопируй ссылку на **raw**-версию конфига:
   
2. Открой **Shadowrocket** → вкладка **Config** → **+** → **Add from URL**

3. Вставь ссылку → **Save**

4. На вкладке **Home** выбери **Global Routing → Config**

5. Включи VPN

## 🔄 Обновление конфига

Конфиг обновляется в репозитории **каждый час**, но Shadowrocket не подтягивает изменения автоматически. Чтобы получить свежую версию:

- **Долгое нажатие** на конфиг во вкладке Config → **Update**

Или просто перезагрузи VPN — иногда конфиг подтягивается сам.

## 📂 Файлы в репозитории

| Файл | Назначение |
|------|------------|
| `generator.py` | Главный скрипт (скачивает списки, пингует домены, генерирует конфиг) |
| `template.conf` | Шаблон конфига с плейсхолдерами |
| `ShadowVoice_Live.conf` | Готовый конфиг (генерируется автоматически) |
| `.github/workflows/main.yml` | GitHub Actions — запуск каждый час |

## 🛠 Что внутри конфига

- **DIRECT**: доступные российские сайты (Госуслуги, банки, ритейл, соцсети)
- **PROXY**: заблокированные сайты (YouTube, Instagram, Telegram, TikTok, OpenAI и др.)
- **REJECT**: рекламные домены
- **Apple**: FaceTime и iCloud через PROXY, AirDrop и локальные сервисы DIRECT
- **Блокировка QUIC**: трафик идёт по TCP для корректной обработки
- **RULE-SET**: автообновляемые списки российских IP и доменов

## 📊 Источники правил

| Тип | Источник |
|-----|----------|
| Российские домены | `roscomvpn-geoip`, `MetaCubeX/geoip` |
| Иностранные сервисы | `blackmatrix7/ios_rule_script` |
| Реклама | `blackmatrix7/ios_rule_script` |

Список иностранных сервисов включает:
- Google, YouTube, Gmail
- Instagram, Facebook, Twitter/X
- TikTok
- OpenAI / ChatGPT
- Telegram
- Netflix
- Discord
- GitHub
- Spotify
- Twitch
- Reddit

## ⚙️ Технические детали

- **Проверка доступности:** DNS (`dns.resolver`) + HTTPS (`requests`)
- **Многопоточность:** 30 потоков
- **Таймаут:** 5 секунд на домен
- **Лимит доменов для пинга:** до 800 (чтобы не превышать лимиты GitHub Actions)
- **Форсированные правила:** отдельные домены принудительно отправляются в DIRECT или PROXY

## 🧪 Ручной запуск генерации

Перейди во вкладку **Actions** → **Generate Config** → **Run workflow**

## 📄 Лицензия

MIT

---

## ⚠️ Примечание

Если репозиторий **приватный**, raw-ссылка не будет работать в Shadowrocket.  
Сделай репозиторий **публичным** или используй публичный репозиторий для хранения конфига.

---

## 🙏 Благодарности

- [blackmatrix7](https://github.com/blackmatrix7/ios_rule_script) за качественные списки правил
- [hydraponique](https://github.com/hydraponique/roscomvpn-geoip) за российские GeoIP
- [MetaCubeX](https://github.com/MetaCubeX/meta-rules-dat) за дополнительные списки
