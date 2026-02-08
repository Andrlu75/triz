# Инструкция для агентов-разработчиков — ТРИЗ-Решатель

> Эта инструкция предназначена для агентов (субпроцессов Claude Code), которые **одновременно** работают над разными задачами одного проекта. Прочитай полностью перед началом работы.

---

## 1. Обзор проекта

**ТРИЗ-Решатель** — AI-платформа решения изобретательских задач по АРИЗ-2010 (В. Петров).

**Стек:** Django 5 + DRF, React + TypeScript + Vite + Tailwind, OpenAI GPT-4o, PostgreSQL + pgvector, Celery + Redis, Docker Compose.

### Ключевые файлы (только чтение)

| Файл | Назначение |
|------|-----------|
| `implementation-plan.md` | **Эталон реализации** — что именно создавать, какие классы, методы, поля |
| `triz-solver-architecture.md` | Архитектура — 6 уровней, модели, API, промпт-иерархия |
| `triz-solver-spec.html` | Визуализация ТЗ + task list (статусы, исполнители, прогресс) |
| `auditor-instructions.md` | Инструкция для аудитора (не для тебя, но полезно знать процесс) |

---

## 2. Идентификация агента

Каждый агент получает **уникальный ID** на основе системной задачи, которую он выполняет.

**Формат:** `agent-{sysId}`

| ID агента | Задача | Область |
|-----------|--------|---------|
| `agent-48` | #48 | Инфраструктура, Docker |
| `agent-49` | #49 | Модели данных |
| `agent-50` | #50 | LLM-сервис (OpenAI) |
| `agent-51` | #51 | АРИЗ-движок |
| `agent-52` | #52 | REST API |
| `agent-53` | #53 | Промпты Jinja2 |
| `agent-54` | #54 | Фронтенд каркас |
| `agent-55` | #55 | Чат-интерфейс |
| `agent-56` | #56 | Решения + адаптив |
| `agent-57` | #57 | База знаний |
| `agent-58` | #58 | Векторный поиск |
| `agent-59` | #59 | Полный АРИЗ-2010 |
| `agent-60` | #60 | Отчёты PDF/DOCX |
| `agent-61` | #61 | Команды + биллинг |

> Один агент = одна системная задача. Не бери больше одной задачи.

---

## 3. Два task list и синхронизация

### Системный task list (14 задач)

Управляется через `TaskList`, `TaskGet`, `TaskUpdate`. Это **агрегированные задачи** — каждая покрывает группу из 7–18 подзадач (одну «неделю»).

### HTML task list (156 подзадач)

Файл `triz-solver-spec.html`, массив `taskList` в JavaScript-коде. Каждая группа имеет поле `sysId` — привязка к системной задаче.

### Правило синхронизации

> **При любом обновлении статуса — обновлять ОБА: системный task list И HTML-файл.**

---

## 4. Маппинг системных задач ↔ HTML

| Сис. задача | sysId | HTML-группа | Подзадачи | Файлы (scope) |
|---|---|---|---|---|
| #48 | `[48]` | ФАЗА 0 | 0.1–0.13 | `docker-compose.yml`, `Makefile`, `backend/Dockerfile`, `frontend/Dockerfile`, `backend/config/`, `backend/requirements/`, `.env.example` |
| #49 | `[49]` | Неделя 1 | 1.1–1.14 | `backend/apps/users/models.py`, `backend/apps/problems/models.py`, `backend/apps/ariz_engine/models.py`, `apps/*/admin.py`, `tests/test_models.py` |
| #50 | `[50]` | Неделя 2 | 1.15–1.26 | `backend/apps/llm_service/client.py`, `backend/apps/llm_service/prompt_manager.py`, `backend/apps/llm_service/tasks.py`, `tests/test_llm_client.py`, `tests/test_prompts.py`, `tests/test_tasks.py` |
| #51 | `[51]` | Неделя 3 | 1.27–1.44 | `backend/apps/ariz_engine/engine.py`, `backend/apps/ariz_engine/steps/registry.py`, `backend/apps/ariz_engine/modes/`, `backend/apps/ariz_engine/validators/`, `tests/test_engine.py`, `tests/test_validators.py` |
| #52 | `[52, 53]` | Неделя 4 (API) | 1.45–1.52 | `backend/apps/*/serializers.py`, `backend/apps/*/views.py`, `backend/config/urls.py`, `tests/test_api.py` |
| #53 | `[52, 53]` | Неделя 4 (промпты) | 1.53–1.61 | `backend/prompts/**/*.j2` |
| #54 | `[54]` | Неделя 5 | 2.1–2.12 | `frontend/src/api/`, `frontend/src/store/`, `frontend/src/pages/{Home,Login,Register,Dashboard,NewProblem}Page.tsx`, `frontend/src/components/layout/` |
| #55 | `[55]` | Неделя 6 | 2.13–2.22 | `frontend/src/pages/SessionPage.tsx`, `frontend/src/components/session/`, `frontend/src/hooks/`, `frontend/src/components/common/` |
| #56 | `[56]` | Неделя 7 | 2.23–2.31 | `frontend/src/components/solutions/`, `frontend/src/pages/SummaryPage.tsx`, `frontend/src/__tests__/` |
| #57 | `[57]` | Неделя 8 | 3.1–3.14 | `backend/apps/knowledge_base/models.py`, `backend/apps/knowledge_base/fixtures/*.json`, `backend/apps/knowledge_base/management/commands/` |
| #58 | `[58]` | Неделя 9 | 3.15–3.26 | `backend/apps/llm_service/embeddings.py`, `backend/apps/knowledge_base/search.py`, `backend/apps/knowledge_base/views.py`, `tests/test_vector_search.py`, `tests/test_knowledge_api.py` |
| #59 | `[59]` | Неделя 10 | 4.1–4.8 | `backend/apps/ariz_engine/modes/full.py`, `backend/prompts/steps/full/` |
| #60 | `[60]` | Неделя 11 | 4.9–4.15 | `backend/apps/reports/` |
| #61 | `[61]` | Неделя 12 | 4.16–4.25 | `backend/apps/users/billing.py`, `frontend/src/pages/PricingPage.tsx`, `tests/test_full_*`, `tests/test_plan_limits.py` |

---

## 5. Захват задачи (протокол)

Несколько агентов работают одновременно. Чтобы не было конфликтов:

### Правило: первый захватил — тот и делает

```
1. TaskList → найти задачу со статусом "pending" и БЕЗ blockedBy
2. TaskGet(taskId) → убедиться, что owner пустой
3. TaskUpdate(taskId, status="in_progress", owner="agent-{sysId}")  ← ЗАХВАТ
4. Только после успешного захвата — начинать работу
```

### Что делать если задача уже занята

Если `TaskGet` показывает, что у задачи уже есть `owner` — **не трогать**, взять другую.

### Что делать если нет доступных задач

Если все незаблокированные задачи заняты — сообщить пользователю и завершить работу.

---

## 6. Владение файлами

### Принцип: каждый агент работает ТОЛЬКО со своими файлами

Колонка «Файлы (scope)» в таблице маппинга (раздел 4) определяет, какие файлы принадлежат какому агенту.

### Общие файлы (shared)

Некоторые файлы редактируются несколькими агентами:

| Файл | Кто редактирует | Протокол |
|------|----------------|---------|
| `backend/config/settings/base.py` | agent-48 создаёт, другие дополняют `INSTALLED_APPS` | Добавлять только свой app, не трогать чужие строки |
| `backend/config/urls.py` | agent-52 создаёт основу, другие дополняют | Добавлять только свои `include()`, не трогать чужие |
| `backend/requirements/base.txt` | agent-48 создаёт, другие дополняют | Добавлять только свои пакеты в конец файла |
| `triz-solver-spec.html` | все агенты обновляют статусы | См. раздел 8 |

### Правила для общих файлов

1. **Перечитай файл** перед каждым редактированием (Read → Edit)
2. **Добавляй** свои строки, **не удаляй** чужие
3. **Используй минимальный Edit** — меняй только то, что нужно
4. При конфликте — **сообщи пользователю**, не перезаписывай

---

## 7. Workflow агента

### Шаг 1: Инициализация

```
1. Прочитать implementation-plan.md — найти свою фазу/неделю
2. Прочитать triz-solver-architecture.md — понять общую архитектуру
3. TaskList → выбрать задачу
4. TaskGet(taskId) → прочитать описание
```

### Шаг 2: Захват задачи

```
TaskUpdate(taskId, status="in_progress", owner="agent-{sysId}")
```

### Шаг 3: Отметить подзадачи в HTML

Найти свою группу в `triz-solver-spec.html` по `sysId` и отметить все подзадачи:

```
Было:
    { id: "0.1", title: "...", file: "...", priority: "high", hours: 0.5 },

Стало:
    { id: "0.1", title: "...", file: "...", priority: "high", hours: 0.5, status: "in_progress", owner: "agent-48" },
```

> **Внимание:** редактируй ТОЛЬКО строки своей группы. Не трогай строки других групп.

### Шаг 4: Выполнить работу

- Создавать файлы и код **строго по `implementation-plan.md`**
- Следовать архитектуре из `triz-solver-architecture.md`
- Писать тесты, если они предусмотрены планом
- Создавать только файлы из своего scope (раздел 4)

### Шаг 5: Отмечать подзадачи по мере выполнения

Каждую завершённую подзадачу обновлять в HTML:

```
Было:
    { id: "0.1", ..., status: "in_progress", owner: "agent-48" },

Стало:
    { id: "0.1", ..., status: "completed", owner: "agent-48" },
```

### Шаг 6: Завершить системную задачу

Когда **ВСЕ** подзадачи группы имеют `status: "completed"`:

```
TaskUpdate(taskId, status="completed")
```

Задача переходит к аудитору на проверку.

---

## 8. Работа с HTML-файлом (параллельный доступ)

Файл `triz-solver-spec.html` — единый dashboard для всех агентов и аудитора. Несколько агентов могут редактировать его одновременно.

### Правила безопасного редактирования

1. **Всегда перечитывай** файл перед каждым Edit (Read → Edit)
2. **Редактируй только свои строки** — задачи своей группы (по sysId)
3. **Используй уникальный old_string** — включай `id: "X.Y"` для точного попадания
4. **Не меняй** структуру HTML, CSS, React-компоненты, чужие группы
5. **Один Edit = одна подзадача** — не пытайся обновить несколько строк одним Edit

### Пример безопасного Edit

```
Edit файл: triz-solver-spec.html

old_string:
    { id: "1.5", title: "Модель Problem (title, mode, domain, status)", file: "apps/problems/models.py", priority: "high", hours: 2 },

new_string:
    { id: "1.5", title: "Модель Problem (title, mode, domain, status)", file: "apps/problems/models.py", priority: "high", hours: 2, status: "completed", owner: "agent-49" },
```

> `id: "1.5"` гарантирует уникальность — в файле нет двух задач с одинаковым id.

---

## 9. Зависимости между задачами

```
#48 Фаза 0: Docker + инфраструктура          ← СТАРТОВАЯ (нет зависимостей)
 ├─► #49 Фаза 1.1: Модели данных             ← blocked by #48
 │    ├─► #51 Фаза 1.3: АРИЗ-движок          ← blocked by #49, #50
 │    │    ├─► #52 Фаза 1.4: REST API         ← blocked by #49, #51
 │    │    │    └─► #54 Фаза 2.1: Фронтенд    ← blocked by #52
 │    │    │         └─► #55 Фаза 2.2: Чат     ← blocked by #54
 │    │    │              └─► #56 Фаза 2.3     ← blocked by #55
 │    │    ├─► #60 Фаза 4.2: Отчёты           ← blocked by #51
 │    │    └─► #59 Фаза 4.1: Полный АРИЗ      ← blocked by #51, #53, #58
 │    └─► #57 Фаза 3.1: База знаний           ← blocked by #49
 │         └─► #58 Фаза 3.2: Вект. поиск      ← blocked by #57, #50
 └─► #50 Фаза 1.2: LLM-сервис                ← blocked by #48
      └─► #53 Фаза 1.4: Промпты              ← blocked by #50

#61 Фаза 4.3: Финал                          ← blocked by #56, #59, #60
```

### Максимальный параллелизм по волнам

| Волна | Задачи | Агенты |
|-------|--------|--------|
| 1 | #48 | 1 агент |
| 2 | #49, #50 | 2 агента параллельно |
| 3 | #51, #53, #57 | 3 агента параллельно |
| 4 | #52, #58, #60 | 3 агента параллельно |
| 5 | #54, #59 | 2 агента параллельно |
| 6 | #55 | 1 агент |
| 7 | #56 | 1 агент |
| 8 | #61 | 1 агент |

> **ВАЖНО:** Не начинать задачу, пока все её `blockedBy` не имеют статус `completed` (или `verified`). Проверять через `TaskGet(taskId)`.

---

## 10. Взаимодействие с другими агентами

### Ты зависишь от чужой работы

Если твоя задача заблокирована (`blockedBy`) — **не начинай**. Дождись завершения блокирующей задачи.

Проверка:
```
TaskGet(taskId) → посмотреть blockedBy → все должны быть completed
```

### Другие зависят от твоей работы

Твои файлы могут быть нужны другим агентам. Поэтому:

1. **Создавай файлы полностью** — не оставляй пустые заглушки
2. **Экспортируй** всё, что указано в плане (классы, функции, константы)
3. **Следуй именованию** из `implementation-plan.md` — другие агенты будут импортировать по этим именам
4. **Завершай быстро** — ты блокируешь других

### Конфликт или вопрос

Если обнаружил проблему, которая выходит за scope твоей задачи:
- **Не исправляй** чужой код
- **Сообщи пользователю** через текстовое сообщение
- Укажи: какой файл, какая проблема, какой агент должен исправить

---

## 11. Статусы задач

| Статус | Метка в HTML | Цвет | Кто ставит |
|--------|-------------|------|-----------|
| `pending` | PENDING | Серый | — |
| `in_progress` | IN PROGRESS | Голубой | Агент |
| `completed` | ON REVIEW | Янтарный | Агент |
| `verified` | ✓ OK | Ярко-зелёный | Аудитор |
| `fix_required` | ⚠ FIX | Красный | Аудитор |

### Жизненный цикл

```
pending → in_progress → completed → verified ✓
                              ↓
                        fix_required → in_progress → completed → verified ✓
```

### Поля задачи в HTML

| Поле | Кто заполняет | Описание |
|------|--------------|----------|
| `status` | Агент / Аудитор | Текущий статус |
| `owner` | Агент | ID агента (`agent-48`, `agent-49`, ...) |
| `reviewer` | Аудитор | ID аудитора |
| `reviewNote` | Аудитор | Описание проблемы (при `fix_required`) |

---

## 12. Исправление замечаний аудитора

Если аудитор поставил `fix_required`:

1. Прочитать `reviewNote` — что именно не так
2. Исправить проблему в коде
3. Обновить HTML: `status: "completed"` (оставить `reviewer` и `reviewNote` как есть)
4. Аудитор повторно проверит

```
Было:
    { id: "0.5", ..., status: "fix_required", owner: "agent-48", reviewer: "auditor", reviewNote: "..." },

Стало:
    { id: "0.5", ..., status: "completed", owner: "agent-48", reviewer: "auditor", reviewNote: "..." },
```

---

## 13. Правила

### Код

- Следовать `implementation-plan.md` — не добавлять лишнего
- Следовать `triz-solver-architecture.md` — не менять архитектуру
- Работать только со своими файлами (scope из раздела 4)
- Не оставлять `TODO`, `pass`, пустых заглушек
- Не хардкодить секреты (API-ключи, пароли)

### Тесты

- Писать тесты, указанные в плане
- Запускать перед завершением: `pytest` (backend), `npm test` (frontend)

### Коммиты

- **Не коммитить** без запроса пользователя
- **Не пушить** без явного разрешения

### Общение

- Все сообщения — **на русском языке**
- Техническая документация в коде — на английском (стандарт Django/React)

---

## 14. Чеклист агента

### Перед началом

- [ ] Прочитал эту инструкцию полностью
- [ ] Прочитал `implementation-plan.md` — нашёл свою фазу/неделю
- [ ] Проверил `TaskList` — выбрал незаблокированную задачу без owner
- [ ] Прочитал описание через `TaskGet`
- [ ] Захватил задачу: `TaskUpdate(status="in_progress", owner="agent-{sysId}")`

### Во время работы

- [ ] Отметил подзадачи в HTML (`status: "in_progress"`, `owner`)
- [ ] Создаю файлы только из своего scope
- [ ] Перечитываю HTML перед каждым Edit
- [ ] Обновляю подзадачи в HTML по мере выполнения (`status: "completed"`)

### После завершения

- [ ] Все подзадачи группы: `status: "completed"` в HTML
- [ ] Системная задача: `TaskUpdate(status="completed")`
- [ ] Тесты проходят
- [ ] Не осталось TODO/pass заглушек
- [ ] Задача готова к проверке аудитором
