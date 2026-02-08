import { useState } from "react";

const colors = {
  bg: "#0a0e17",
  card: "#111827",
  cardHover: "#1a2332",
  border: "#1e293b",
  borderActive: "#3b82f6",
  text: "#e2e8f0",
  textMuted: "#94a3b8",
  textDim: "#64748b",
  accent: "#3b82f6",
  accentLight: "#60a5fa",
  green: "#10b981",
  greenDark: "#064e3b",
  amber: "#f59e0b",
  amberDark: "#78350f",
  purple: "#8b5cf6",
  purpleDark: "#4c1d95",
  rose: "#f43f5e",
  roseDark: "#881337",
  cyan: "#06b6d4",
  cyanDark: "#164e63",
};

const layers = [
  {
    id: "clients",
    title: "КЛИЕНТСКИЙ СЛОЙ",
    color: colors.cyan,
    bgColor: colors.cyanDark,
    items: [
      { name: "Web SPA", tech: "React + TS", icon: "🌐", desc: "Основной интерфейс для B2C и B2B. Чат-диалог с визуализацией шагов АРИЗ, прогресс-бар, карточки решений." },
      { name: "PWA Mobile", tech: "Progressive Web App", icon: "📱", desc: "Мобильная версия через PWA. Тот же React, адаптивный дизайн, оффлайн-доступ к истории задач." },
      { name: "Telegram Bot", tech: "Telegram Bot API", icon: "🤖", desc: "Быстрый вход для B2C. Упрощённый Краткий АРИЗ в формате чат-бота. Минимальный порог входа." },
    ],
  },
  {
    id: "api",
    title: "API GATEWAY",
    color: colors.accent,
    bgColor: "#1e3a5f",
    items: [
      { name: "REST API", tech: "Django + DRF", icon: "⚡", desc: "Основной API. Эндпоинты: /problems, /sessions, /steps, /solutions. JWT-авторизация, rate limiting." },
      { name: "WebSocket", tech: "Django Channels", icon: "🔄", desc: "Реалтайм-обновления для пошагового режима. Стриминг ответов LLM, уведомления о завершении анализа." },
      { name: "Async Tasks", tech: "Celery + Redis", icon: "⏳", desc: "Фоновые задачи: LLM-вызовы (длительные), генерация отчётов, поиск аналогов, переиндексация." },
    ],
  },
  {
    id: "core",
    title: "АРИЗ-ENGINE (ЯДРО)",
    color: colors.green,
    bgColor: colors.greenDark,
    items: [
      { name: "Экспресс", tech: "Краткий АРИЗ (7 шагов)", icon: "🚀", desc: "B2C-режим. Цепочка: ПП → УП → ИКР → ОП → Решение. Диалоговый формат, ТРИЗ-терминология скрыта от пользователя." },
      { name: "Полный АРИЗ-2010", tech: "4 части, ~30 шагов", icon: "🔬", desc: "B2B-режим. Полная реализация: Анализ задачи → Анализ ресурсов → Определение ОП → Получение решения. 28 правил валидации." },
      { name: "Автопилот", tech: "LLM Chain", icon: "🤖", desc: "LLM проходит все шаги автоматически. Пользователь вводит задачу → получает структурированный отчёт с решением." },
      { name: "Валидаторы", tech: "28 правил Петрова", icon: "✅", desc: "Проверка формулировок: ГФ (правила 4-11), УП (правило 19), спецтермины (правило 15), усиление (правила 22-24)." },
    ],
  },
  {
    id: "llm",
    title: "LLM-СЕРВИС",
    color: colors.purple,
    bgColor: colors.purpleDark,
    items: [
      { name: "Prompt Manager", tech: "Jinja2 Templates", icon: "📝", desc: "Иерархия промптов: System → Role → Methodology → Step → Validation → Audience Adapter. Версионирование промптов." },
      { name: "Claude API", tech: "Sonnet 4", icon: "🧠", desc: "Основная LLM. ~$0.02-0.05 за экспресс-задачу, ~$0.10-0.30 за полный АРИЗ. Стриминг ответов." },
      { name: "Knowledge RAG", tech: "pgvector + embeddings", icon: "🔍", desc: "Поиск задач-аналогов по вектору ОП. Подбор релевантных приёмов и эффектов из информационного фонда ТРИЗ." },
    ],
  },
  {
    id: "knowledge",
    title: "ИНФОРМАЦИОННЫЙ ФОНД ТРИЗ",
    color: colors.amber,
    bgColor: colors.amberDark,
    items: [
      { name: "40+10 приёмов", tech: "JSON + Embeddings", icon: "💡", desc: "40 основных приёмов устранения ТП + 10 дополнительных. Таблица применения приёмов. Парные приёмы-антиприёмы." },
      { name: "Эффекты", tech: "Физ/Хим/Био/Геом", icon: "⚗️", desc: "Указатели технологических эффектов: физические, химические, биологические, геометрические. Таблица функция→эффект." },
      { name: "Стандарты", tech: "76 стандартов", icon: "📐", desc: "Система стандартов на решение изобретательских задач. 5 классов стандартов для вепольного анализа." },
      { name: "Задачи-аналоги", tech: "Векторная БД", icon: "🗃️", desc: "База разобранных задач (Глава 6 + расширение). Векторный поиск по формулировке ОП. Фонд решений." },
    ],
  },
  {
    id: "data",
    title: "ХРАНИЛИЩЕ ДАННЫХ",
    color: colors.rose,
    bgColor: colors.roseDark,
    items: [
      { name: "PostgreSQL", tech: "Основная БД", icon: "🗄️", desc: "Пользователи, задачи, АРИЗ-сессии, результаты шагов, противоречия, ИКР, решения. pgvector для эмбеддингов." },
      { name: "Redis", tech: "Кэш + Очереди", icon: "⚡", desc: "Состояние АРИЗ-сессий, кэш промптов, очереди Celery, rate limiting, JWT-сессии." },
      { name: "S3 / MinIO", tech: "Файлы", icon: "📦", desc: "Сгенерированные отчёты (PDF/DOCX), загруженные пользователем файлы, экспорт данных." },
    ],
  },
];

const arizFlow = [
  { step: "Ввод задачи", desc: "Пользователь описывает проблему", color: colors.textMuted },
  { step: "Проверка на ложность", desc: "5 пунктов проверки", color: colors.amber },
  { step: "ПП", desc: "Поверхностное противоречие", color: colors.cyan },
  { step: "УП", desc: "Углублённое противоречие", color: colors.accent },
  { step: "ИКР", desc: "Идеальный конечный результат", color: colors.green },
  { step: "ОП", desc: "Обострённое противоречие", color: colors.purple },
  { step: "Решение", desc: "Разрешение через приёмы/эффекты", color: colors.rose },
];

export default function ArchitectureDiagram() {
  const [activeLayer, setActiveLayer] = useState(null);
  const [activeItem, setActiveItem] = useState(null);
  const [view, setView] = useState("architecture");

  return (
    <div style={{ background: colors.bg, minHeight: "100vh", color: colors.text, fontFamily: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace" }}>
      {/* Header */}
      <div style={{ padding: "24px 32px", borderBottom: `1px solid ${colors.border}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <span style={{ fontSize: 28 }}>⚡</span>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, letterSpacing: "-0.5px" }}>
            ТРИЗ-Решатель
          </h1>
          <span style={{ fontSize: 11, color: colors.textDim, background: colors.card, padding: "3px 10px", borderRadius: 4, border: `1px solid ${colors.border}` }}>
            v1.0 Architecture
          </span>
        </div>
        <p style={{ margin: 0, fontSize: 13, color: colors.textMuted }}>
          AI-powered система решения задач по методологии АРИЗ-2010 (В. Петров)
        </p>

        {/* View Tabs */}
        <div style={{ display: "flex", gap: 4, marginTop: 16 }}>
          {[
            { id: "architecture", label: "Архитектура системы" },
            { id: "flow", label: "АРИЗ Flow" },
            { id: "stack", label: "Tech Stack" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => { setView(tab.id); setActiveLayer(null); setActiveItem(null); }}
              style={{
                padding: "8px 16px",
                fontSize: 12,
                fontWeight: 600,
                fontFamily: "inherit",
                background: view === tab.id ? colors.accent : "transparent",
                color: view === tab.id ? "#fff" : colors.textMuted,
                border: `1px solid ${view === tab.id ? colors.accent : colors.border}`,
                borderRadius: 6,
                cursor: "pointer",
                transition: "all 0.2s",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: "24px 32px" }}>
        {view === "architecture" && (
          <div style={{ display: "flex", gap: 24 }}>
            {/* Layers */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12 }}>
              {layers.map((layer, li) => (
                <div key={layer.id}>
                  {/* Layer Header */}
                  <div
                    onClick={() => { setActiveLayer(activeLayer === layer.id ? null : layer.id); setActiveItem(null); }}
                    style={{
                      padding: "12px 16px",
                      background: activeLayer === layer.id ? layer.bgColor : colors.card,
                      border: `1px solid ${activeLayer === layer.id ? layer.color : colors.border}`,
                      borderRadius: activeLayer === layer.id ? "8px 8px 0 0" : 8,
                      cursor: "pointer",
                      transition: "all 0.2s",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <div style={{ width: 4, height: 24, background: layer.color, borderRadius: 2 }} />
                      <span style={{ fontSize: 13, fontWeight: 700, color: layer.color, letterSpacing: "0.5px" }}>
                        {layer.title}
                      </span>
                    </div>
                    <span style={{ fontSize: 11, color: colors.textDim }}>
                      {layer.items.length} компонентов
                    </span>
                  </div>

                  {/* Layer Items */}
                  {activeLayer === layer.id && (
                    <div style={{
                      border: `1px solid ${layer.color}`,
                      borderTop: "none",
                      borderRadius: "0 0 8px 8px",
                      background: colors.card,
                      padding: 8,
                      display: "flex",
                      flexWrap: "wrap",
                      gap: 8,
                    }}>
                      {layer.items.map((item, ii) => (
                        <div
                          key={ii}
                          onClick={(e) => { e.stopPropagation(); setActiveItem(activeItem?.name === item.name ? null : item); }}
                          style={{
                            flex: "1 1 180px",
                            padding: "10px 12px",
                            background: activeItem?.name === item.name ? layer.bgColor : colors.bg,
                            border: `1px solid ${activeItem?.name === item.name ? layer.color : colors.border}`,
                            borderRadius: 6,
                            cursor: "pointer",
                            transition: "all 0.15s",
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                            <span style={{ fontSize: 16 }}>{item.icon}</span>
                            <span style={{ fontSize: 12, fontWeight: 600 }}>{item.name}</span>
                          </div>
                          <div style={{ fontSize: 10, color: colors.textDim }}>{item.tech}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Connector */}
                  {li < layers.length - 1 && (
                    <div style={{ display: "flex", justifyContent: "center", padding: "4px 0" }}>
                      <div style={{ width: 2, height: 12, background: colors.border }} />
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Detail Panel */}
            <div style={{
              width: 320,
              position: "sticky",
              top: 24,
              alignSelf: "flex-start",
            }}>
              {activeItem ? (
                <div style={{
                  background: colors.card,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 8,
                  padding: 20,
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                    <span style={{ fontSize: 24 }}>{activeItem.icon}</span>
                    <div>
                      <div style={{ fontSize: 15, fontWeight: 700 }}>{activeItem.name}</div>
                      <div style={{ fontSize: 11, color: colors.accent }}>{activeItem.tech}</div>
                    </div>
                  </div>
                  <p style={{ fontSize: 13, color: colors.textMuted, lineHeight: 1.6, margin: 0 }}>
                    {activeItem.desc}
                  </p>
                </div>
              ) : (
                <div style={{
                  background: colors.card,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 8,
                  padding: 20,
                  textAlign: "center",
                }}>
                  <div style={{ fontSize: 32, marginBottom: 8 }}>👈</div>
                  <p style={{ fontSize: 12, color: colors.textDim, margin: 0 }}>
                    Кликните на слой, затем на компонент для просмотра деталей
                  </p>
                </div>
              )}

              {/* Architecture stats */}
              <div style={{
                background: colors.card,
                border: `1px solid ${colors.border}`,
                borderRadius: 8,
                padding: 16,
                marginTop: 12,
              }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: colors.textDim, marginBottom: 12, letterSpacing: "1px" }}>
                  СТАТИСТИКА
                </div>
                {[
                  { label: "Слоёв архитектуры", value: "6" },
                  { label: "Компонентов", value: "20" },
                  { label: "Шагов АРИЗ-2010", value: "~30" },
                  { label: "Правил валидации", value: "28" },
                  { label: "Приёмов ТРИЗ", value: "50+" },
                  { label: "Стоимость запроса", value: "$0.02-0.30" },
                ].map((stat, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: i < 5 ? `1px solid ${colors.border}` : "none" }}>
                    <span style={{ fontSize: 11, color: colors.textMuted }}>{stat.label}</span>
                    <span style={{ fontSize: 11, fontWeight: 700, color: colors.accent }}>{stat.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {view === "flow" && (
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4, color: colors.text }}>
              Логика АРИЗ — цепочка решения
            </h2>
            <p style={{ fontSize: 12, color: colors.textDim, marginBottom: 24 }}>
              Основная цепочка: ПП → УП → ИКР → ОП → Решение. Каждый шаг углубляет причинно-следственный анализ.
            </p>

            {/* Flow diagram */}
            <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
              {arizFlow.map((step, i) => (
                <div key={i}>
                  <div style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 16,
                    padding: "16px 20px",
                    background: colors.card,
                    border: `1px solid ${colors.border}`,
                    borderRadius: 8,
                  }}>
                    <div style={{
                      width: 36,
                      height: 36,
                      borderRadius: "50%",
                      background: step.color + "20",
                      border: `2px solid ${step.color}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 14,
                      fontWeight: 800,
                      color: step.color,
                      flexShrink: 0,
                    }}>
                      {i + 1}
                    </div>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: step.color }}>{step.step}</div>
                      <div style={{ fontSize: 12, color: colors.textMuted }}>{step.desc}</div>
                    </div>
                    {i < arizFlow.length - 1 && (
                      <div style={{ marginLeft: "auto", fontSize: 11, color: colors.textDim, whiteSpace: "nowrap" }}>
                        {i === 0 ? "формализация" : i === 1 ? "фильтр" : i <= 3 ? "углубление" : i === 4 ? "направление" : i === 5 ? "обострение" : ""}
                      </div>
                    )}
                  </div>
                  {i < arizFlow.length - 1 && (
                    <div style={{ display: "flex", alignItems: "center", paddingLeft: 37 }}>
                      <div style={{ width: 2, height: 20, background: colors.border }} />
                      <span style={{ fontSize: 16, marginLeft: -6, color: colors.border }}>▾</span>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Modes comparison */}
            <h3 style={{ fontSize: 14, fontWeight: 700, marginTop: 32, marginBottom: 16 }}>Три режима работы</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
              {[
                {
                  title: "🚀 Экспресс",
                  audience: "B2C",
                  steps: "7 шагов",
                  time: "5-10 мин",
                  cost: "~$0.03",
                  desc: "Краткий АРИЗ. ТРИЗ-термины скрыты. Диалоговый формат.",
                  color: colors.green,
                },
                {
                  title: "🔬 Полный АРИЗ",
                  audience: "B2B",
                  steps: "~30 шагов",
                  time: "30-60 мин",
                  cost: "~$0.20",
                  desc: "Все 4 части АРИЗ-2010. Полная терминология. Отчёт PDF.",
                  color: colors.purple,
                },
                {
                  title: "🤖 Автопилот",
                  audience: "Все",
                  steps: "Авто",
                  time: "1-3 мин",
                  cost: "~$0.10",
                  desc: "LLM проходит АРИЗ сам. Быстрый результат. Меньше глубины.",
                  color: colors.amber,
                },
              ].map((mode, i) => (
                <div key={i} style={{
                  background: colors.card,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 8,
                  padding: 16,
                  borderTop: `3px solid ${mode.color}`,
                }}>
                  <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>{mode.title}</div>
                  <div style={{ fontSize: 12, color: colors.textMuted, marginBottom: 12, lineHeight: 1.5 }}>{mode.desc}</div>
                  {[
                    { label: "Аудитория", value: mode.audience },
                    { label: "Шагов", value: mode.steps },
                    { label: "Время", value: mode.time },
                    { label: "Стоимость", value: mode.cost },
                  ].map((row, ri) => (
                    <div key={ri} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderTop: `1px solid ${colors.border}` }}>
                      <span style={{ fontSize: 11, color: colors.textDim }}>{row.label}</span>
                      <span style={{ fontSize: 11, fontWeight: 600, color: mode.color }}>{row.value}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {view === "stack" && (
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>Технологический стек</h2>
            <p style={{ fontSize: 12, color: colors.textDim, marginBottom: 24 }}>
              Подобран под твой опыт с Django + DRF, React + TS, Telegram Bot API
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12 }}>
              {[
                { category: "Backend", items: [
                  { name: "Django 5 + DRF", why: "Основной стек, зрелый, знакомый" },
                  { name: "Celery + Redis", why: "Async LLM-вызовы, фоновые задачи" },
                  { name: "Django Channels", why: "WebSocket для стриминга ответов" },
                  { name: "PostgreSQL + pgvector", why: "Данные + векторный поиск аналогов" },
                ], color: colors.green },
                { category: "Frontend", items: [
                  { name: "React + TypeScript", why: "SPA, компонентный подход" },
                  { name: "Tailwind CSS", why: "Быстрая стилизация" },
                  { name: "Framer Motion", why: "Анимации переходов между шагами" },
                  { name: "Lovable.dev (MVP)", why: "Быстрый прототип фронтенда" },
                ], color: colors.cyan },
                { category: "AI / ML", items: [
                  { name: "Claude API (Sonnet 4)", why: "Лучшее качество/цена для анализа" },
                  { name: "Jinja2 Templates", why: "Шаблонизация 30+ промптов" },
                  { name: "pgvector Embeddings", why: "Поиск задач-аналогов по ОП" },
                  { name: "LangChain (optional)", why: "Оркестрация цепочек вызовов" },
                ], color: colors.purple },
                { category: "Инфраструктура", items: [
                  { name: "Render.com", why: "Быстрый деплой для MVP" },
                  { name: "Redis Cloud", why: "Managed кэш и очереди" },
                  { name: "S3 / MinIO", why: "Хранение отчётов" },
                  { name: "Sentry + PostHog", why: "Мониторинг + аналитика" },
                ], color: colors.amber },
              ].map((cat, ci) => (
                <div key={ci} style={{
                  background: colors.card,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 8,
                  overflow: "hidden",
                }}>
                  <div style={{
                    padding: "10px 16px",
                    background: cat.color + "15",
                    borderBottom: `1px solid ${colors.border}`,
                    fontSize: 13,
                    fontWeight: 700,
                    color: cat.color,
                  }}>
                    {cat.category}
                  </div>
                  {cat.items.map((item, ii) => (
                    <div key={ii} style={{
                      padding: "10px 16px",
                      borderBottom: ii < cat.items.length - 1 ? `1px solid ${colors.border}` : "none",
                    }}>
                      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 2 }}>{item.name}</div>
                      <div style={{ fontSize: 11, color: colors.textDim }}>{item.why}</div>
                    </div>
                  ))}
                </div>
              ))}
            </div>

            {/* MVP Timeline */}
            <h3 style={{ fontSize: 14, fontWeight: 700, marginTop: 32, marginBottom: 16 }}>MVP Roadmap (12 недель)</h3>
            <div style={{ display: "flex", gap: 8 }}>
              {[
                { phase: "Ядро", weeks: "4 нед", tasks: "Django + АРИЗ-Engine + Claude API + Промпты", color: colors.green },
                { phase: "Фронтенд", weeks: "3 нед", tasks: "React SPA + чат-интерфейс + визуализация шагов", color: colors.cyan },
                { phase: "Knowledge", weeks: "2 нед", tasks: "40 приёмов + эффекты + задачи-аналоги + RAG", color: colors.amber },
                { phase: "B2B", weeks: "3 нед", tasks: "Полный АРИЗ + отчёты + биллинг + команды", color: colors.purple },
              ].map((p, i) => (
                <div key={i} style={{
                  flex: `${parseInt(p.weeks)} 1 0`,
                  background: colors.card,
                  border: `1px solid ${colors.border}`,
                  borderTop: `3px solid ${p.color}`,
                  borderRadius: 8,
                  padding: 12,
                }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: p.color }}>{p.phase}</div>
                  <div style={{ fontSize: 10, color: colors.textDim, marginBottom: 6 }}>{p.weeks}</div>
                  <div style={{ fontSize: 11, color: colors.textMuted, lineHeight: 1.4 }}>{p.tasks}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
