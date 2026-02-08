# План реализации ТРИЗ-Решатель (Full MVP)

## Контекст

Проект ТРИЗ-Решатель — ИИ-платформа для решения задач по методологии АРИЗ-2010 (книга В. Петрова). Архитектура описана в `triz-solver-architecture.md`. Нужно реализовать полный MVP: все 3 режима АРИЗ (Экспресс, Полный, Автопилот), бэкенд + фронтенд + база знаний + B2B-расширения. Деплой локально через Docker Compose.

---

## ФАЗА 0: Инфраструктура (2-3 дня)

### 0.1. Docker Compose

**Файл**: `docker-compose.yml`

Сервисы:
- `backend` — Django 5, порт 8000
- `celery_worker` — Celery worker для LLM-вызовов
- `celery_beat` — Celery beat (периодические задачи)
- `db` — PostgreSQL 16 с pgvector (`pgvector/pgvector:pg16`)
- `redis` — Redis 7 (кэш + очереди Celery)
- `frontend` — React (Vite), порт 5173

**Файл**: `docker-compose.dev.yml` — оверрайд для разработки (hot-reload, debug)

### 0.2. Структура каталогов

```
triz/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── .gitignore
├── Makefile
├── backend/
│   ├── Dockerfile
│   ├── requirements/
│   │   ├── base.txt          # django, drf, celery, openai, jinja2, psycopg, redis
│   │   └── dev.txt           # pytest, ruff, factory-boy, pytest-django
│   ├── manage.py
│   └── config/
│       ├── __init__.py
│       ├── settings/
│       │   ├── base.py       # общие настройки
│       │   └── dev.py        # DEBUG=True, CORS, локальные БД
│       ├── urls.py
│       ├── wsgi.py
│       ├── asgi.py
│       └── celery.py         # конфигурация Celery
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── ...
```

### 0.3. Makefile

Команды: `make up`, `make down`, `make logs`, `make migrate`, `make test`, `make shell`, `make load-triz`

### 0.4. Переменные окружения (.env.example)

```
DJANGO_SECRET_KEY=...
OPENAI_API_KEY=...
DATABASE_URL=postgres://triz:triz@db:5432/triz_solver
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
```

---

## ФАЗА 1: Ядро (4 недели)

### Неделя 1.1: Модели данных

#### `backend/apps/users/models.py`
```python
class User(AbstractUser):
    plan = CharField(choices=["free","pro","business"], default="free")
    organization = ForeignKey(Organization, null=True)
    locale = CharField(default="ru")

class Organization:
    name, created_at
```

#### `backend/apps/problems/models.py`
```python
class Problem:
    user (FK→User)
    title, original_description
    mode: "express" | "full" | "autopilot"
    domain: "technical" | "business" | "everyday"
    status: "draft" | "in_progress" | "completed" | "archived"
    final_report (JSONField)
    created_at, updated_at
```

#### `backend/apps/ariz_engine/models.py`
```python
class ARIZSession:
    problem (FK→Problem)
    mode: "express" | "full" | "autopilot"
    current_step (CharField)        # "1" / "1.1" / "1.1.1" и т.д.
    current_part (IntegerField)     # 1-4 для полного АРИЗ
    context_snapshot (JSONField)    # агрегированный контекст для LLM
    status: "active" | "completed" | "abandoned"
    completed_at

class StepResult:
    session (FK→ARIZSession)
    step_code (CharField)           # "1", "2", ... или "1.1", "1.2", ...
    step_name (CharField)
    user_input (TextField)
    llm_output (TextField)
    validated_result (TextField)
    validation_notes (TextField)
    status: "pending" | "in_progress" | "completed" | "failed"
    created_at

class Contradiction:
    session (FK→ARIZSession)
    type: "surface" | "deepened" | "sharpened"
    quality_a, quality_b (CharField)
    property_s, anti_property_s (CharField)
    formulation (TextField)

class IKR:
    session (FK→ARIZSession)
    formulation (TextField)
    strengthened_formulation (TextField)
    vpr_used (JSONField)

class Solution:
    session (FK→ARIZSession)
    method_used (CharField)         # "principle" | "standard" | "effect" | ...
    title, description (TextField)
    novelty_score (1-10)
    feasibility_score (1-10)
```

### Неделя 1.2: LLM-сервис

#### `backend/apps/llm_service/client.py`
- Класс `OpenAIClient` — обёртка над `openai.OpenAI`
- Модель: GPT-4o (основная) / GPT-4o-mini (валидация, снижение стоимости)
- Метод `send_message(system_prompt, messages, max_tokens)` → response
- Метод `create_embedding(text)` → vector (text-embedding-3-small, dim=1536)
- Подсчёт стоимости: `calculate_cost(input_tokens, output_tokens)`
- Retry-логика: 3 попытки с экспоненциальным backoff
- Timeout: 120 сек

#### `backend/apps/llm_service/prompt_manager.py`
- Класс `PromptManager` — загрузка и рендеринг Jinja2-шаблонов
- `render_system_prompt(mode, audience)` → собирает master + role + methodology + adapter
- `render_step_prompt(step_code, context)` → рендерит шаблон шага с контекстом
- `render_validation_prompt(rule_codes, content)` → промпт для валидации
- Путь к шаблонам: `backend/prompts/`

#### `backend/apps/llm_service/tasks.py`
- Celery-задача `execute_ariz_step(session_id, step_code, user_input)`
  1. Загружает контекст сессии (предыдущие шаги)
  2. Рендерит системный + шаговый промпт
  3. Вызывает OpenAI API (GPT-4o)
  4. Прогоняет через валидатор
  5. Сохраняет StepResult
  6. Обновляет context_snapshot сессии

### Неделя 1.3: АРИЗ-движок

#### `backend/apps/ariz_engine/engine.py` — КЛЮЧЕВОЙ ФАЙЛ
```python
class ARIZEngine:
    """Оркестратор АРИЗ-сессии. Управляет state machine шагов."""

    def __init__(self, session: ARIZSession): ...

    def start_session(self) -> StepResult:
        """Инициализирует сессию, возвращает первый шаг."""

    def submit_step(self, user_input: str) -> str:
        """Принимает ввод пользователя, запускает Celery-задачу.
        Возвращает task_id для polling."""

    def advance_to_next(self) -> StepResult | None:
        """Переходит к следующему шагу (после завершения текущего)."""

    def go_back(self) -> StepResult | None:
        """Возврат на предыдущий шаг."""

    def get_progress(self) -> dict:
        """Возвращает {current_step, total_steps, percent, steps_completed[]}."""

    def get_session_summary(self) -> dict:
        """Полная сводка: задача, все шаги, противоречия, ИКР, решения."""
```

#### `backend/apps/ariz_engine/steps/registry.py`
```python
# Реестр шагов — единственный источник правды о flow АРИЗ

EXPRESS_STEPS = [
    StepDef(code="1", name="Формулировка задачи", prompt="steps/express/step_1.j2",
            validators=["falseness_check"]),
    StepDef(code="2", name="Поверхностное противоречие", prompt="steps/express/step_2.j2",
            validators=["terms_check"]),
    StepDef(code="3", name="Углублённое противоречие", prompt="steps/express/step_3.j2",
            validators=["contradiction_check"]),
    StepDef(code="4", name="Идеальный конечный результат", prompt="steps/express/step_4.j2",
            validators=["ikr_check"]),
    StepDef(code="5", name="Обострённое противоречие", prompt="steps/express/step_5.j2",
            validators=["conflict_check"]),
    StepDef(code="6", name="Углубление ОП", prompt="steps/express/step_6.j2", validators=[]),
    StepDef(code="7", name="Решение", prompt="steps/express/step_7.j2", validators=[]),
]

FULL_STEPS = [
    StepDef(code="1.1", name="Мини-задача", ...), # ~24 шага
    ...
    StepDef(code="4.8", name="Метод ММЧ", ...),
]
```

#### `backend/apps/ariz_engine/modes/express.py`
- Класс `ExpressMode` — логика 7-шагового Краткого АРИЗ
- Переопределяет get_steps(), format_response() (бытовой язык, без терминов)

#### `backend/apps/ariz_engine/modes/full.py`
- Класс `FullARIZMode` — полный АРИЗ-2010, 4 части, ~24 шага
- Подробная терминология, все 28 правил

#### `backend/apps/ariz_engine/modes/autopilot.py`
- Класс `AutopilotMode` — LLM проходит все шаги автоматически
- 1-3 вызова LLM с расширенным контекстом
- Возвращает готовый структурированный отчёт

#### `backend/apps/ariz_engine/validators/base.py`
- `FalsenessValidator` — проверка на ложность (5 пунктов)
- `TermsValidator` — замена спецтерминов (правило 15)
- `ContradictionValidator` — формулировка УП (правило 19)
- `ConflictAmplificationValidator` — усиление конфликта (правила 22-24)
- `FunctionValidator` — формулировка ГФ (правила 4-11)
- `IKRValidator` — формулировка ИКР

### Неделя 1.4: REST API + Промпты

#### API-эндпоинты (`backend/apps/*/views.py` + `config/urls.py`)

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/v1/auth/register/` | Регистрация |
| POST | `/api/v1/auth/login/` | JWT-авторизация |
| POST | `/api/v1/auth/refresh/` | Обновление токена |
| GET | `/api/v1/problems/` | Список задач пользователя |
| POST | `/api/v1/problems/` | Создать задачу |
| GET | `/api/v1/problems/{id}/` | Детали задачи |
| POST | `/api/v1/sessions/start/` | Начать АРИЗ-сессию `{problem_id, mode}` |
| GET | `/api/v1/sessions/{id}/` | Состояние сессии |
| GET | `/api/v1/sessions/{id}/progress/` | Прогресс `{current_step, percent, steps[]}` |
| POST | `/api/v1/sessions/{id}/submit/` | Отправить ввод `{user_input}` → `{task_id}` |
| GET | `/api/v1/sessions/{id}/task/{task_id}/` | Статус Celery-задачи |
| GET | `/api/v1/sessions/{id}/current-step/` | Текущий шаг + результат LLM |
| POST | `/api/v1/sessions/{id}/advance/` | Перейти к следующему шагу |
| POST | `/api/v1/sessions/{id}/back/` | Вернуться на предыдущий шаг |
| GET | `/api/v1/sessions/{id}/summary/` | Полная сводка сессии |

#### Промпты (`backend/prompts/`)

```
prompts/
├── system/
│   ├── master.j2              # Базовый системный промпт
│   ├── role.j2                # "Эксперт ТРИЗ с 30-летним опытом"
│   └── methodology.j2         # 35 определений + 28 правил + логика АРИЗ
├── steps/
│   ├── express/
│   │   ├── step_1.j2          # Формулировка задачи
│   │   ├── step_2.j2          # Поверхностное противоречие (ПП)
│   │   ├── step_3.j2          # Углублённое противоречие (УП)
│   │   ├── step_4.j2          # Идеальный конечный результат (ИКР)
│   │   ├── step_5.j2          # Обострённое противоречие (ОП)
│   │   ├── step_6.j2          # Углубление ОП (ОП₁)
│   │   └── step_7.j2          # Решение
│   ├── full/
│   │   ├── step_1_1.j2 ... step_4_8.j2   # ~24 файла
│   └── autopilot/
│       └── full_analysis.j2   # Один большой промпт для автопилота
├── validation/
│   ├── validate_falseness.j2  # Проверка на ложность
│   ├── validate_function.j2   # Правила 4-11
│   ├── validate_terms.j2      # Правило 15
│   ├── validate_contradiction.j2  # Правило 19
│   ├── validate_conflict.j2   # Правила 22-24
│   └── validate_ikr.j2        # Проверка ИКР
└── adapters/
    ├── b2c.j2                 # Бытовой язык, без терминов
    └── b2b.j2                 # Полная ТРИЗ-терминология
```

---

## ФАЗА 2: Фронтенд (3 недели)

### Стек: React + TypeScript + Vite + Tailwind CSS + Zustand

### Неделя 2.1: Каркас + Авторизация

#### Структура `frontend/src/`
```
src/
├── main.tsx, App.tsx
├── api/
│   ├── client.ts          # axios instance с JWT interceptor
│   ├── types.ts           # TypeScript-типы (Problem, Session, Step, Solution)
│   ├── auth.ts            # login, register, refresh
│   ├── problems.ts        # CRUD задач
│   └── sessions.ts        # start, submit, advance, progress, summary
├── store/
│   ├── authStore.ts       # Zustand: user, token, login/logout
│   └── sessionStore.ts    # Zustand: текущая сессия, шаги, решения
├── hooks/
│   ├── useAuth.ts
│   ├── useSession.ts
│   └── useStepPolling.ts  # Polling статуса Celery-задачи (1s → 2s → 3s backoff)
├── components/ (см. ниже)
├── pages/ (см. ниже)
└── utils/
    ├── formatters.ts
    └── constants.ts
```

#### Страницы (`pages/`)
- `HomePage.tsx` — лендинг с описанием + CTA
- `LoginPage.tsx` / `RegisterPage.tsx` — авторизация
- `DashboardPage.tsx` — список задач пользователя
- `NewProblemPage.tsx` — создание задачи (выбор режима)
- `SessionPage.tsx` — **ГЛАВНАЯ СТРАНИЦА** — чат-интерфейс АРИЗ
- `SummaryPage.tsx` — итоговый отчёт с решениями

### Неделя 2.2: Чат-интерфейс (SessionPage)

#### Ключевые компоненты:

**`components/session/ChatInterface.tsx`**
- Отображает диалог: сообщения LLM + ввод пользователя
- Автоскролл к последнему сообщению
- Markdown-рендеринг ответов LLM

**`components/session/StepProgress.tsx`**
- Вертикальный прогресс-бар с шагами АРИЗ
- Текущий шаг подсвечен, пройденные — зелёные
- Клик на пройденный шаг — просмотр результата

**`components/session/UserInput.tsx`**
- Textarea для ввода + кнопка отправки
- Подсказки контекстные для каждого шага
- Disabled во время обработки LLM

**`components/session/ThinkingIndicator.tsx`**
- Анимированный индикатор "LLM думает..."
- Показывается во время polling Celery-задачи

**`components/session/LLMResponse.tsx`**
- Карточка ответа LLM с Markdown
- Badge валидации (прошёл/не прошёл)

### Неделя 2.3: Решения + Адаптивный дизайн

**`components/solutions/SolutionCard.tsx`**
- Карточка решения: название, описание, метод
- Оценки: новизна и реализуемость (шкала 1-10)
- Цветовая индикация по методу решения

**`components/solutions/SolutionList.tsx`**
- Список решений с сортировкой (по новизне / реализуемости)

**Адаптивный дизайн:**
- Mobile-first через Tailwind breakpoints
- На мобильных: StepProgress сворачивается в горизонтальную полосу
- Чат занимает полную ширину

---

## ФАЗА 3: Информационный фонд (2 недели)

### Неделя 3.1: Модели + Загрузка данных

#### `backend/apps/knowledge_base/models.py`
```python
class TRIZPrinciple:
    number (1-50), name, description, examples (JSONField)
    is_additional (bool)      # 40 основных + 10 дополнительных
    paired_with (FK→self)     # приём-антиприём

class TechnologicalEffect:
    type: "physical" | "chemical" | "biological" | "geometrical"
    name, description, function_keywords (JSONField)
    embedding (VectorField, dim=1536)

class Standard:
    class_number (1-5), number, name, description
    applicability (TextField)

class AnalogTask:
    title, problem_description
    op_formulation (TextField)     # формулировка ОП
    solution_principle (TextField)
    domain, source
    embedding (VectorField, dim=1536)

class Definition:
    number (1-35), term, definition (из Приложения 4)

class Rule:
    number (1-28), name, description, examples (JSONField)

class TypicalTransformation:
    contradiction_type, transformation, description
```

#### `backend/apps/knowledge_base/fixtures/`
JSON-файлы с данными ТРИЗ:
- `principles.json` — 50 приёмов
- `paired_principles.json` — пары приём-антиприём
- `effects_physical.json`, `effects_chemical.json`, `effects_biological.json`, `effects_geometrical.json`
- `standards.json` — 76 стандартов
- `definitions.json` — 35 определений
- `rules.json` — 28 правил
- `typical_transformations.json`
- `analog_tasks.json` — задачи-аналоги из Главы 6

#### `backend/apps/knowledge_base/management/commands/load_triz_data.py`
- Management-команда `python manage.py load_triz_data --all`
- Загрузка из JSON-файлов в БД
- Генерация эмбеддингов через OpenAI Embeddings API (text-embedding-3-small)

### Неделя 3.2: Векторный поиск + API

#### `backend/apps/knowledge_base/search.py`
```python
class TRIZKnowledgeSearch:
    def search_analog_tasks(self, op_formulation: str, top_k=5) -> list[AnalogTask]:
        """Поиск задач-аналогов по формулировке ОП через pgvector."""

    def suggest_principles(self, contradiction: Contradiction) -> list[TRIZPrinciple]:
        """Предложить приёмы на основе типа противоречия."""

    def find_effects(self, function_description: str) -> list[TechnologicalEffect]:
        """Поиск подходящих эффектов по описанию функции."""
```

#### `backend/apps/llm_service/embeddings.py`
- Генерация эмбеддингов через OpenAI Embeddings API (модель: text-embedding-3-small, dim=1536)
- Батчевая генерация: до 2048 текстов за один запрос
- Кэширование эмбеддингов в Redis

#### API-эндпоинты (Фаза 3):

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/v1/knowledge/principles/` | Список приёмов |
| GET | `/api/v1/knowledge/principles/{id}/` | Детали приёма |
| GET | `/api/v1/knowledge/effects/` | Поиск эффектов `?q=...` |
| GET | `/api/v1/knowledge/standards/` | Стандарты |
| GET | `/api/v1/knowledge/analogs/search/` | Поиск аналогов `?q=...&top_k=5` |
| GET | `/api/v1/knowledge/definitions/` | 35 определений |
| GET | `/api/v1/knowledge/rules/` | 28 правил |

---

## ФАЗА 4: B2B расширение (3 недели)

### Неделя 4.1: Полный АРИЗ-2010

- Реализация `backend/apps/ariz_engine/modes/full.py`
- ~24 шага в 4 частях (все промпты `prompts/steps/full/`)
- Часть 1: Анализ задачи (шаги 1.1–1.7) — 16 правил
- Часть 2: Анализ ресурсов (шаги 2.1–2.3)
- Часть 3: Определение ОП (шаги 3.1–3.6)
- Часть 4: Получение решения (шаги 4.1–4.8)
- Интеграция базы знаний в шаги Части 4 (поиск аналогов, приёмы, эффекты)

### Неделя 4.2: Генерация отчётов

#### `backend/apps/reports/generators/pdf_generator.py`
- Класс `PDFReportGenerator(session)` — через ReportLab
- Структура: титул → задача → шаги по частям → решения с оценками
- Кириллица: шрифт DejaVu Sans / PT Sans

#### `backend/apps/reports/generators/docx_generator.py`
- Класс `DOCXReportGenerator(session)` — через python-docx
- Аналогичная структура, редактируемый формат

#### API:
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/v1/reports/{session_id}/download/pdf/` | Скачать PDF |
| GET | `/api/v1/reports/{session_id}/download/docx/` | Скачать DOCX |

### Неделя 4.3: Командная работа + Биллинг

#### Командная работа:
- Модель `OrganizationMembership` (admin / member / viewer)
- Модель `ProblemShare` (view / comment / edit)
- Фильтрация задач по организации

#### Биллинг (простой, без платёжных систем):
- `backend/apps/users/billing.py` — лимиты по планам:
  - **Free**: 5 задач/мес, только Express
  - **Pro**: 50 задач/мес, Express + Autopilot, отчёты
  - **Business**: безлимит, все режимы, команды, отчёты
- Middleware для проверки лимитов

---

## Порядок миграций БД

```
1. users      0001 — User, Organization
2. problems   0001 — Problem
3. ariz_engine 0001 — ARIZSession, StepResult, Contradiction, IKR, Solution
4. knowledge_base 0001 — CREATE EXTENSION vector
5. knowledge_base 0002 — TRIZPrinciple, Effect, Standard, AnalogTask, Definition, Rule
6. users      0002 — OrganizationMembership (Фаза 4)
7. problems   0002 — ProblemShare (Фаза 4)
```

---

## Паттерн оркестрации шага АРИЗ

```
POST /submit → создать StepResult(status=IN_PROGRESS)
             → execute_ariz_step.delay(session_id, step_code, user_input)
             → вернуть 202 {task_id}

Celery task:
  1. Загрузить context_snapshot из ARIZSession
  2. PromptManager.render_system_prompt(mode, audience)
  3. PromptManager.render_step_prompt(step_code, context)
  4. OpenAIClient.send_message(system, messages)  # GPT-4o
  5. Validator.validate(step_code, response)
  6. Сохранить StepResult(validated_result=...)
  7. Обновить ARIZSession.context_snapshot

Фронтенд:
  Polling GET /task/{id}/ каждые 1-3 сек (backoff)
  → получить результат → показать в чате
```

---

## Стратегия тестирования

**Фаза 1 (бэкенд):**
- `tests/test_models.py` — создание моделей, связи
- `tests/test_engine.py` — ARIZEngine: start, advance, go_back (мок Celery)
- `tests/test_prompts.py` — рендеринг промптов, наличие файлов
- `tests/test_llm_client.py` — OpenAIClient (мок openai API)
- `tests/test_tasks.py` — Celery-задачи (мок OpenAI + валидатор)
- `tests/test_validators.py` — rule-based валидаторы
- `tests/test_api.py` — все эндпоинты через DRF APIClient

**Фаза 2 (фронтенд):**
- `ChatInterface.test.tsx`, `StepProgress.test.tsx`, `SolutionCard.test.tsx`
- `useStepPolling.test.ts` — polling логика

**Фаза 3:**
- `test_vector_search.py` — pgvector поиск
- `test_load_triz_data.py` — загрузка данных

**Фаза 4 (E2E):**
- `test_full_express_flow.py` — полный цикл Express: создание → 7 шагов → решение
- `test_report_generation.py` — PDF + DOCX
- `test_plan_limits.py` — лимиты тарифов

---

## Верификация

Как проверить, что всё работает:

1. `make up` — Docker Compose запускается без ошибок
2. `make migrate` — миграции проходят
3. `make test` — все тесты зелёные
4. Создать задачу через API: `POST /api/v1/problems/`
5. Начать сессию: `POST /api/v1/sessions/start/ {problem_id, mode: "express"}`
6. Пройти 7 шагов через `submit` → `task_status` → `advance`
7. Получить summary: `GET /api/v1/sessions/{id}/summary/`
8. Фронтенд: открыть `http://localhost:5173`, создать задачу, пройти диалог
9. Фаза 3: `make load-triz` → проверить поиск аналогов
10. Фаза 4: скачать PDF/DOCX отчёт
