# coding-agents-comparison

Проект для сравнения разных агентов для программирования.

## Структура

- `src/` — код проекта и общие утилиты для сравнения
- `tests/` — тесты
- `.agents/` — локальная папка с реализациями агентов, не хранится в git
- `docs/` — заметки, спецификации и сопроводительная документация
- `.venv/` — рабочее виртуальное окружение на Python 3.12, не хранится в git

## Быстрый старт

Использовать только локальное окружение проекта:

```bash
source .venv/bin/activate
python --version
```

Ожидаемая версия Python:

```bash
Python 3.12.x
```

Если окружение нужно пересоздать:

```bash
rm -rf .venv
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
```

## Принципы

- Работать только через `.venv`.
- Хранить локальные реализации агентов в `.agents/`.
- Не коммитить содержимое `.agents/` и артефакты окружения.

## Текущий набор агентов

Сейчас в `.agents/` лежат такие репозитории:

1. `Hermes Agent` — `.agents/hermes-agent`
2. `Kilo Code` — `.agents/kilocode`
3. `OpenCode` — `.agents/opencode`
4. `Cline` — `.agents/cline`
5. `Qwen Code` — `.agents/qwen-code`
6. `OpenHands` — `.agents/openhands`
7. `Codebuff` — `.agents/codebuff`
8. `Crush` — `.agents/crush`
9. `Aider` — `.agents/aider`
10. `OpenClaw` — `.agents/openclaw`

## Замены относительно исходного топа

- `Claude Code` заменен на `OpenCode`.
- `BLACKBOXAI` заменен на `Aider`.
- `Slate Agent` заменен на `OpenClaw`.

## Спеки

- Основной benchmark-план: [2026-04-21-mediacms-benchmark-plan.md](/Users/ilyagmirin/PycharmProjects/coding-agents-comparison/docs/superpowers/specs/2026-04-21-mediacms-benchmark-plan.md)

## Проверка результатов

- Для каждого benchmark-run сохранять артефакты в `runs/`.
- Обязательный минимум проверки: automated acceptance checks, нормализованный `result.json`, краткая summary.
- Если задача затрагивает UX/UI или любой видимый product surface, browser-level проверка обязательна.
- Для такого browser-check использовать `Playwright` и фиксировать наблюдаемый результат в артефактах run'а.
