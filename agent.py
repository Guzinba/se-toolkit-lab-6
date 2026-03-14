"""
CLI-агент для вызова LLM через OpenAI-compatible API.
Принимает вопрос, возвращает структурированный JSON ответ.
"""

import json
import os
import sys
import argparse
from pathlib import Path

# Используем httpx для async-запросов с таймаутом
try:
    import httpx
except ImportError:
    print("Ошибка: требуется пакет httpx. Установите: uv add httpx", file=sys.stderr)
    sys.exit(1)


def load_env_file(filepath: str) -> dict:
    """Загружает переменные окружения из .env файла."""
    env_vars = {}
    path = Path(filepath)
    if not path.exists():
        print(f"Предупреждение: файл {filepath} не найден", file=sys.stderr)
        return env_vars
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_vars[key.strip()] = value.strip().strip('"\'')
    return env_vars


def call_llm(question: str, config: dict) -> dict:
    """Отправляет запрос к LLM и возвращает ответ."""
    api_base = config.get("LLM_API_BASE", "http://localhost:42005/v1")
    api_key = config.get("LLM_API_KEY", "")
    model = config.get("LLM_MODEL", "qwen3-coder-plus")
    timeout = int(config.get("LLM_TIMEOUT", "60"))
    
    # Формируем системный промпт (минимальный для задачи 1)
    system_prompt = (
        "Ты полезный ассистент. Отвечай кратко и точно на вопросы пользователя. "
        "Форматируй ответ как обычный текст, без маркдауна."
    )
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    url = f"{api_base}/chat/completions"
    
    try:
        print(f"Отправка запроса к {url}...", file=sys.stderr)
        
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        
        # Извлекаем ответ из структуры OpenAI
        if "choices" in data and len(data["choices"]) > 0:
            answer = data["choices"][0]["message"]["content"]
        else:
            raise ValueError("Неожиданная структура ответа от LLM")
        
        return {"ответ": answer.strip(), "вызовы_инструмента": []}
        
    except httpx.TimeoutException:
        print(f"Ошибка: таймаут запроса ({timeout}с)", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"Ошибка сети: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка обработки ответа: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="CLI-агент для вызова LLM")
    parser.add_argument("question", type=str, help="Вопрос для агента")
    args = parser.parse_args()
    
    # Загружаем конфигурацию
    config = load_env_file(".env.agent.secret")
    
    # Вызываем LLM
    result = call_llm(args.question, config)
    
    # Выводим ТОЛЬКО валидный JSON в stdout
    print(json.dumps(result, ensure_ascii=False))
    
    # Успешный выход
    sys.exit(0)


if __name__ == "__main__":
    main()
