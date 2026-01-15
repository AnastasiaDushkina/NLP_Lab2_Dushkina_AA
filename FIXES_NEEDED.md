# Инструкции по исправлению ноутбука

Этот файл содержит список исправлений, которые нужно внести в ноутбук NLP_Lab2_Dushkina_AA.ipynb

## 1. Исправление memory_node (ячейка 22)

Замените функцию `memory_node` на следующую версию, которая записывает данные в память:

```python
def memory_node(state: SystemState) -> dict:
    """Узел памяти: извлекает и обновляет релевантную информацию из истории и базы знаний"""
    query = state.get("user_query", "")
    routing_decision = state.get("routing_decision")
    session_history = state.get("session_history", [])
    knowledge_base = state.get("knowledge_base", {})
    user_profile = state.get("user_profile", {})
    user_preferences = state.get("user_preferences", {})
    
    relevant_context = []
    
    # Извлечение релевантной информации
    if routing_decision and routing_decision.needs_memory:
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for entry in session_history[-10:]:
            entry_query = entry.get("query", "").lower()
            entry_words = set(entry_query.split())
            if len(query_words & entry_words) >= 2:
                relevant_context.append({
                    "type": "history",
                    "query": entry.get("query", ""),
                    "answer": entry.get("answer", "")[:200]
                })

        for key, value in knowledge_base.items():
            if any(word in key.lower() or word in str(value).lower() for word in query_words):
                relevant_context.append({
                    "type": "knowledge",
                    "key": key,
                    "value": str(value)
                })
    
    # Обновление профиля пользователя на основе запроса
    if "игрок" in query.lower() or "игроков" in query.lower():
        import re
        players_match = re.search(r'(\d+)\s*игрок', query.lower())
        if players_match:
            user_profile["preferred_players"] = int(players_match.group(1))
            user_preferences["last_players"] = int(players_match.group(1))
    
    if "минут" in query.lower() or "время" in query.lower():
        import re
        time_match = re.search(r'(\d+)\s*минут', query.lower())
        if time_match:
            user_profile["preferred_duration"] = int(time_match.group(1))
            user_preferences["last_duration"] = int(time_match.group(1))
    
    # Сохранение информации о предпочтениях
    if routing_decision:
        if routing_decision.agent_type == "search":
            user_preferences["last_search_type"] = "game_recommendation"
        elif routing_decision.agent_type == "compare":
            user_preferences["last_search_type"] = "comparison"
    
    # Обновление knowledge_base с информацией о текущем запросе
    if routing_decision:
        query_key = f"query_{len(knowledge_base)}"
        knowledge_base[query_key] = {
            "query": query,
            "agent_type": routing_decision.agent_type,
            "timestamp": datetime.now().isoformat()
        }

    return {
        "knowledge_base": knowledge_base,
        "user_profile": user_profile,
        "user_preferences": user_preferences
    }
```

## 2. Исправление route_after_router (ячейка 38)

Замените функции маршрутизации на следующие:

```python
def route_after_router(state: SystemState) -> str:
    """Определяет следующий узел после роутера"""
    routing_decision = state.get("routing_decision")
    
    if not routing_decision:
        return "theory"
    
    agent_type = routing_decision.agent_type
    
    if routing_decision.needs_planning:
        return "planner"
    elif agent_type == "search":
        return "planner"  # Для search нужен planner чтобы создать план рекомендации
    elif agent_type == "explain":
        return "explain"
    elif agent_type == "compare":
        return "compare"
    elif agent_type == "plan":
        return "planner"
    elif agent_type == "theory":
        return "theory"
    elif agent_type == "code":
        return "code"
    elif agent_type == "general":
        return "theory"
    else:
        return "theory"

def route_after_planner(state: SystemState) -> str:
    """Определяет следующий узел после планировщика"""
    routing_decision = state.get("routing_decision")
    
    if not routing_decision:
        return "game_search"
    
    agent_type = routing_decision.agent_type
    
    if agent_type == "search":
        return "content_filter"  # Для search идем в цепочку фильтрации
    elif agent_type == "plan":
        return "plan"  # Для plan идем в plan узел
    elif agent_type == "code":
        return "code"
    else:
        return "game_search"  # По умолчанию идем в game_search

def route_after_merge(state: SystemState) -> str:
    """Определяет следующий узел после объединения результатов"""
    return "game_search"
```

## 3. Исправление графа (ячейка 40)

Замените создание графа на следующую версию:

```python
workflow = StateGraph(SystemState)

# Добавляем все узлы
workflow.add_node("router", router_node)
workflow.add_node("memory", memory_node)
workflow.add_node("planner", planner_node)
workflow.add_node("content_filter", content_filter_node)
workflow.add_node("metadata_filter", metadata_filter_node)
workflow.add_node("merge_results", merge_results_node)
workflow.add_node("game_search", game_search_node)
workflow.add_node("explain", explain_node)
workflow.add_node("compare", compare_node)
workflow.add_node("plan", plan_node)
workflow.add_node("theory", theory_node)
workflow.add_node("code", code_node)
workflow.add_node("update_memory", update_memory_node)
workflow.add_node("final_response", final_response_node)

# Начало графа
workflow.add_edge(START, "router")

# После роутера всегда идем в memory
workflow.add_edge("router", "memory")

# После memory маршрутизация в зависимости от типа агента
workflow.add_conditional_edges(
    "memory",
    route_after_router,
    {
        "planner": "planner",
        "explain": "explain",
        "compare": "compare",
        "plan": "plan",
        "theory": "theory",
        "code": "code",
        "content_filter": "content_filter"
    }
)

# После planner маршрутизация для search или plan
workflow.add_conditional_edges(
    "planner",
    route_after_planner,
    {
        "content_filter": "content_filter",
        "plan": "plan",
        "code": "code",
        "game_search": "game_search"
    }
)

# Цепочка фильтрации для search
workflow.add_edge("content_filter", "metadata_filter")
workflow.add_edge("metadata_filter", "merge_results")
workflow.add_edge("merge_results", "game_search")

# Все агенты идут в update_memory
workflow.add_edge("game_search", "update_memory")
workflow.add_edge("explain", "update_memory")
workflow.add_edge("compare", "update_memory")
workflow.add_edge("plan", "update_memory")
workflow.add_edge("theory", "update_memory")
workflow.add_edge("code", "update_memory")

# После обновления памяти идем в final_response
workflow.add_edge("update_memory", "final_response")
workflow.add_edge("final_response", END)

app = workflow.compile()

print("Граф создан со всеми узлами")
```

## 4. Исправление update_memory_node (ячейка 34)

Замените функцию `update_memory_node` на следующую версию:

```python
def update_memory_node(state: SystemState) -> dict:
    """Обновляет память системы после получения ответа"""
    query = state.get("user_query", "")
    agent_response = state.get("agent_response")
    routing_decision = state.get("routing_decision")
    session_history = state.get("session_history", [])
    knowledge_base = state.get("knowledge_base", {})
    
    new_entry = {
        "query": query,
        "answer": agent_response.answer if agent_response else "",
        "agent": routing_decision.agent_type if routing_decision else "unknown",
        "timestamp": datetime.now().isoformat()
    }
    session_history.append(new_entry)

    if agent_response and agent_response.memory_updates:
        key = f"topic_{len(knowledge_base)}"
        knowledge_base[key] = agent_response.memory_updates
    
    # Обновление user_profile и user_preferences на основе ответа
    user_profile = state.get("user_profile", {})
    user_preferences = state.get("user_preferences", {})
    recommendation_history = state.get("recommendation_history", [])
    
    # Сохранение рекомендованных игр в историю
    if agent_response and agent_response.recommended_games:
        recommendation_history.extend(agent_response.recommended_games)
        # Обновление предпочтений на основе рекомендованных игр
        for game in agent_response.recommended_games:
            if "preferred_genres" not in user_preferences:
                user_preferences["preferred_genres"] = []
            user_preferences["preferred_genres"].extend(game.genres)
            if "preferred_mechanics" not in user_preferences:
                user_preferences["preferred_mechanics"] = []
            user_preferences["preferred_mechanics"].extend(game.mechanics)
    
    # Обновление профиля на основе использованных инструментов
    if agent_response and agent_response.used_tools:
        user_profile["last_used_tools"] = agent_response.used_tools
    
    return {
        "session_history": session_history,
        "knowledge_base": knowledge_base,
        "user_profile": user_profile,
        "user_preferences": user_preferences,
        "recommendation_history": recommendation_history
    }
```

## 5. Исправление run_system (ячейка 44)

Замените функцию `run_system` на следующую версию:

```python
def run_system(query: str, user_id: str = "user1", state: Optional[SystemState] = None) -> dict:
    """Запускает мультиагентную систему с запросом пользователя"""

    if state is None:
        initial_state: SystemState = {
            "user_query": query,
            "user_id": user_id,
            "routing_decision": None,
            "recommendation_plan": None,
            "action_plan": None,
            "content_filtered": [],
            "metadata_filtered": [],
            "final_games": [],
            "agent_response": None,
            "session_history": [],
            "user_preferences": {},
            "user_profile": {},
            "recommendation_history": [],
            "knowledge_base": {},
            "final_answer": "",
            "execution_path": []
        }
    else:
        initial_state = state
        initial_state["user_query"] = query
    
    result = app.invoke(initial_state)
    
    return result
```

## 6. Добавление демонстрации работы памяти

Добавьте новую ячейку после экспериментов с демонстрацией работы памяти:

```python
# Демонстрация работы памяти
print("=== Демонстрация работы памяти ===\n")

# Первый запрос
query_mem1 = "Найди игру для 4 игроков на 60 минут"
result_mem1 = run_system(query_mem1)
print(f"Запрос 1: {query_mem1}")
print(f"Профиль пользователя после запроса 1: {result_mem1.get('user_profile', {})}")
print(f"Предпочтения: {result_mem1.get('user_preferences', {})}")
print(f"База знаний: {list(result_mem1.get('knowledge_base', {}).keys())}")
print()

# Второй запрос с использованием памяти
query_mem2 = "А теперь найди игру для 2 игроков"
result_mem2 = run_system(query_mem2, state=result_mem1)
print(f"Запрос 2: {query_mem2}")
print(f"Профиль пользователя после запроса 2: {result_mem2.get('user_profile', {})}")
print(f"Предпочтения: {result_mem2.get('user_preferences', {})}")
print(f"История сессии: {len(result_mem2.get('session_history', []))} записей")
print(f"Рекомендованные игры в истории: {len(result_mem2.get('recommendation_history', []))} игр")
print()

# Третий запрос - проверка использования памяти
query_mem3 = "Какие игры я искал раньше?"
result_mem3 = run_system(query_mem3, state=result_mem2)
print(f"Запрос 3: {query_mem3}")
print(f"Ответ системы использует память: {result_mem3.get('routing_decision', {}).needs_memory if result_mem3.get('routing_decision') else False}")
print(f"База знаний содержит: {len(result_mem3.get('knowledge_base', {}))} записей")
```

## Резюме исправлений

1. ✅ Добавлена модель ActionPlan
2. ✅ Добавлены поля user_profile и action_plan в SystemState
3. ✅ Созданы LangChain tools (search_game_by_name, get_games_by_criteria, calculate_game_time, compare_games_info)
4. ✅ Созданы узлы explain_node, compare_node, plan_node
5. ⚠️ Нужно исправить memory_node для записи данных
6. ⚠️ Нужно исправить маршрутизацию для всех типов агентов
7. ⚠️ Нужно обновить граф для включения всех узлов
8. ⚠️ Нужно исправить update_memory_node для обновления памяти
9. ⚠️ Нужно исправить run_system для правильной инициализации
10. ✅ Обновлен README для соответствия реальной архитектуре



