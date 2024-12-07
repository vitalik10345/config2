# Визуализатор зависимостей пакетов Ubuntu

## Общее описание

Этот проект реализует инструмент командной строки для построения и визуализации графа зависимостей пакетов операционной системы Ubuntu с использованием Graphviz. Визуализатор анализирует зависимости указанного пакета, включая транзитивные зависимости, и выводит результат в виде кода Graphviz DOT. Инструмент позволяет пользователю исследовать структуру зависимостей пакетов Ubuntu, задавая различные параметры через конфигурационный файл.

---

## Функции и настройки

### Основные функции

- **Построение графа зависимостей пакетов Ubuntu:**
  - Визуализация зависимостей между пакетами в формате Graphviz.
  - Включение транзитивных зависимостей до заданной глубины.

- **Гибкая настройка через конфигурационный файл:**
  - Указание пути к программе для визуализации графов (`dot`).
  - Задание максимальной глубины анализа зависимостей.
  - Указание имени анализируемого пакета и пути к файлу-результату.

- **Вывод результатов:**
  - Генерация DOT-кода для визуализации графа зависимостей.
  - Сохранение результата в указанный файл.
  - Вывод DOT-кода непосредственно в консоль.

### Конфигурационный файл (`config.json`)

Конфигурационный файл позволяет настраивать параметры работы визуализатора. Пример содержимого `config.json`:

```json
{
  "graph_tool_path": "/usr/bin/dot",
  "package_name": "curl",
  "output_file": "output.dot",
  "max_depth": 2,
  "repository_url": "http://archive.ubuntu.com/ubuntu"
}
```
### Параметры командной строки

- `graph_tool_path`: Путь к программе Graphviz (`dot`) для генерации графов.
- `package_name`: Имя пакета Ubuntu, зависимости которого необходимо проанализировать.
- `output_file`: Путь к файлу для сохранения сгенерированного DOT-кода.
- `max_depth`: Максимальная глубина анализа транзитивных зависимостей.
- `repository_url`: URL-адрес репозитория Ubuntu (может использоваться для справочных целей).

### Реализация функций
1. **`load_config` Считывает конфигурационный файл и возвращает его содержимое:** 
```python
    def load_config(config_path: str) -> Dict:
    with open(config_path, 'r') as f:
        return json.load(f)

```
2. **`get_dependencies` Получает список прямых зависимостей указанного пакета с помощью команды `apt-cache`:** 
```python
    def get_dependencies(package: str) -> List[str]:
    try:
        output = subprocess.check_output(["apt-cache", "depends", package], text=True)
    except subprocess.CalledProcessError:
        return []

    deps = []
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith("Depends:") or line.startswith("PreDepends:"):
            part = line.split(":", 1)[1].strip()
            pkg_name = part.split()[0]
            deps.append(pkg_name)
    return deps
```
3. **`build_dependency_graph` Строит граф зависимостей пакета до заданной глубины:**
```python
    def build_dependency_graph(package: str, max_depth: int) -> Dict[str, Set[str]]:
    graph = {}
    visited = set()

    def dfs(pkg: str, depth: int):
        if depth > max_depth:
            return
        if pkg in visited:
            return
        visited.add(pkg)
        deps = get_dependencies(pkg)
        graph[pkg] = set(deps)
        for d in deps:
            dfs(d, depth + 1)

    dfs(package, 0)
    return graph
```
  
4. **`generate_dot_code` Преобразует граф зависимостей в формат DOT для визуализации:**
```python
    def generate_dot_code(graph: Dict[str, Set[str]], root_package: str) -> str:
    lines = ["digraph G {"]
    lines.append(f'    label="{root_package} dependencies";')
    lines.append('    labelloc="t";')
    for pkg, deps in graph.items():
        for d in deps:
            lines.append(f'    "{pkg}" -> "{d}";')
    lines.append("}")
    return "\n".join(lines)
```
5. **Основная функция main:**
```python
    def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <config_path>")
        sys.exit(1)

    config_path = sys.argv[1]
    config = load_config(config_path)

    graph_tool_path = config.get("graph_tool_path")
    package_name = config.get("package_name")
    output_file = config.get("output_file")
    max_depth = config.get("max_depth", 1)
    repository_url = config.get("repository_url")
    
    graph = build_dependency_graph(package_name, max_depth)
    dot_code = generate_dot_code(graph, package_name)
    with open(output_file, "w") as f:
        f.write(dot_code)
    print(dot_code)
```
5. **`def mock_config_file(tmp_path)` Фикстура для создания временного конфигурационного файла:**
```python
    config_data = {
        "graph_tool_path": "/usr/bin/dot",
        "package_name": "curl",
        "output_file": str(tmp_path / "output.dot"),
        "max_depth": 1,
        "repository_url": "http://archive.ubuntu.com/ubuntu"
    }
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(config_data, f)
    return config_path
```
7. **`def test_load_config(mock_config_file)`Тестирование функции load_config:**
```python
    config = load_config(str(mock_config_file))
    assert config["package_name"] == "curl"
    assert config["max_depth"] == 1
```

9.  **`def test_get_dependencies(mock_check_output)` Тестирование функции get_dependencies с использованием моков:**
   ```python
    mock_output = """curl
    Depends: libcurl4 (= 7.68.0-1ubuntu2.12)
    Depends: libc6 (>= 2.17)
    Recommends: ca-certificates
  
    mock_check_output.return_value = mock_output
    deps = get_dependencies("curl")
    assert "libcurl4" in deps
    assert "libc6" in deps
    assert "ca-certificates" not in deps
  ```  
10. **`def test_build_dependency_graph(mock_get_deps)` Предположим пакет 'A' зависит от 'B' и 'C', 'B' не имеет зависимостей, 'C' зависит от 'D':**

```python
 mock_get_deps.side_effect = lambda p: {"A": ["B", "C"], "C": ["D"], "B": [], "D": []}[p]
    graph = build_dependency_graph("A", 2)
    assert "A" in graph
    assert "B" in graph["A"]
    assert "C" in graph["A"]
    assert "C" in graph
    assert "D" in graph["C"]
    # "D" тоже в графе, так как глубина позволяет
    assert "D" in graph
    # У "B" и "D" зависимостей нет
    assert graph["B"] == set()
    assert graph["D"] == set()
```
11. **`def test_generate_dot_code()` проверяет правильность создания DOT-кода для графа зависимостей:**
```python
 graph = {
        "A": {"B", "C"},
        "B": set(),
        "C": {"D"},
        "D": set()
    }
    dot = generate_dot_code(graph, "A")
    # Проверим ключевые элементы DOT-кода
    assert 'digraph G' in dot
    assert '"A" -> "B";' in dot
    assert '"A" -> "C";' in dot
    assert '"C" -> "D";' in dot
    assert 'label="A dependencies";' in dot
```
## Команды для сборки проекта
1. **Установка зависимостей:**

   Установите необходимые Python-библиотеки:

```bash
   pip3 install pytest
```
2. **Запуск визуализатора:**
```bash
python3 main.py config.json

```
3. **Генерация изображения из DOT-файла:**
```bash
dot -Tpng output.dot -o output.png

```
4. **Запуск тестов:**
```bash
pytest

```


---
 
## Результаты прогонов тестов

**Тестовый файл для проверки всех функций**
```python
import pytest
import json
from unittest.mock import patch

from main import load_config, get_dependencies, build_dependency_graph, generate_dot_code

@pytest.fixture
def mock_config_file(tmp_path):
    config_data = {
        "graph_tool_path": "/usr/bin/dot",
        "package_name": "curl",
        "output_file": str(tmp_path / "output.dot"),
        "max_depth": 1,
        "repository_url": "http://archive.ubuntu.com/ubuntu"
    }
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(config_data, f)
    return config_path

def test_load_config(mock_config_file):
    config = load_config(str(mock_config_file))
    assert config["package_name"] == "curl"
    assert config["max_depth"] == 1

@patch("subprocess.check_output")
def test_get_dependencies(mock_check_output):
    # Мокаем вывод apt-cache depends
    mock_output = """curl
  Depends: libcurl4 (= 7.68.0-1ubuntu2.12)
  Depends: libc6 (>= 2.17)
  Recommends: ca-certificates
"""
    mock_check_output.return_value = mock_output
    deps = get_dependencies("curl")
    # Ожидается что get_dependencies вернёт ['libcurl4', 'libc6']
    # Recommends не считаем зависимостью
    assert "libcurl4" in deps
    assert "libc6" in deps
    assert "ca-certificates" not in deps

@patch("main.get_dependencies")
def test_build_dependency_graph(mock_get_deps):
    # Предположим пакет 'A' зависит от 'B' и 'C', 'B' не имеет зависимостей, 'C' зависит от 'D'.
    # max_depth = 2
    mock_get_deps.side_effect = lambda p: {"A": ["B", "C"], "C": ["D"], "B": [], "D": []}[p]
    graph = build_dependency_graph("A", 2)
    assert "A" in graph
    assert "B" in graph["A"]
    assert "C" in graph["A"]
    assert "C" in graph
    assert "D" in graph["C"]
    # "D" тоже в графе, так как глубина позволяет
    assert "D" in graph
    # У "B" и "D" зависимостей нет
    assert graph["B"] == set()
    assert graph["D"] == set()

def test_generate_dot_code():
    graph = {
        "A": {"B", "C"},
        "B": set(),
        "C": {"D"},
        "D": set()
    }
    dot = generate_dot_code(graph, "A")
    # Проверим несколько ключевых моментов
    assert 'digraph G' in dot
    assert '"A" -> "B";' in dot
    assert '"A" -> "C";' in dot
    assert '"C" -> "D";' in dot
    assert 'label="A dependencies";' in dot
```
**Запуск тестов с помощью**:
````
pytest
````

**Вывод**:

<img width="968" alt="image" src="https://github.com/user-attachments/assets/eb1ed878-1fad-4629-8571-e816b4f3846f">
Все тесты успешно пройдены, что подтверждает корректность работы всех функций визуализатора.
