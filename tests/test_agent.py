"""
Регрессионный тест для agent.py
Проверяет, что агент возвращает валидный JSON с обязательными полями.
"""

import json
import subprocess
import sys
from pathlib import Path


def test_agent_basic_response():
    """Тест: агент отвечает на простой вопрос."""
    
    # Путь к agent.py относительно корня проекта
    project_root = Path(__file__).parent.parent
    agent_path = project_root / "agent.py"
    
    # Команда запуска
    cmd = [
        "uv", "run",
        str(agent_path),
        "Что такое Python?"
    ]
    
    # Запускаем агент как подпроцесс
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=project_root,
        timeout=70  # 60с + запас
    )
    
    # Проверяем код выхода
    assert result.returncode == 0, f"Агент вернул код {result.returncode}\nstderr: {result.stderr}"
    
    # Парсим stdout как JSON
    try:
        output = json.loads(result.stdout.strip())
    except json.JSONDecodeError as e:
        raise AssertionError(f"stdout не является валидным JSON: {e}\nstdout: {result.stdout}")
    
    # Проверяем обязательные поля
    assert "ответ" in output, f"Отсутствует поле 'ответ' в ответе: {output}"
    assert "вызовы_инструмента" in output, f"Отсутствует поле 'вызовы_инструмента' в ответе: {output}"
    
    # Проверяем тип tool_calls
    assert isinstance(output["вызовы_инструмента"], list), "Поле 'вызовы_инструмента' должно быть массивом"
    
    # Проверяем, что ответ не пустой
    assert len(output["ответ"]) > 0, "Поле 'ответ' не должно быть пустым"
    
    print("✅ Тест пройден", file=sys.stderr)
    return True


if __name__ == "__main__":
    try:
        test_agent_basic_response()
        print("Все тесты пройдены!")
        sys.exit(0)
    except AssertionError as e:
        print(f"❌ Тест провален: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка выполнения теста: {e}", file=sys.stderr)
        sys.exit(1)
