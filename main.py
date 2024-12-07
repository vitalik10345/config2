import json
import subprocess
import sys
from typing import Dict, List, Set

def load_config(config_path: str) -> Dict:
    with open(config_path, 'r') as f:
        return json.load(f)

def get_dependencies(package: str) -> List[str]:
    """
    Получить список прямых зависимостей для указанного пакета
    используя команду 'apt-cache depends <package>'.
    Возвращает список имён пакетов-зависимостей.
    """
    try:
        output = subprocess.check_output(["apt-cache", "depends", package], text=True)
        print(f"Output for {package}:\n{output}")  # Для отладки
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving dependencies for {package}: {e}")
        return []

    deps = []
    for line in output.split('\n'):
        line = line.strip()
        # Учитываем локализованные строки зависимостей
        if line.startswith("Depends:") or line.startswith("Зависит:") or line.startswith("PreDepends:"):
            part = line.split(":", 1)[1].strip()  # После ':' берём зависимость
            if part:
                pkg_name = part.split()[0]  # Извлекаем имя пакета
                if pkg_name and pkg_name != package:
                    deps.append(pkg_name)
    return deps


def build_dependency_graph(package: str, max_depth: int) -> Dict[str, Set[str]]:
    """
    Рекурсивно строит граф зависимостей в виде словаря {pkg: {deps}}.
    """
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

def generate_dot_code(graph: Dict[str, Set[str]], root_package: str) -> str:
    """
    Генерирует код в формате DOT для визуализации графа.
    """
    lines = ["digraph G {"]
    lines.append(f'    label="{root_package} dependencies";')
    lines.append('    labelloc="t";')
    for pkg, deps in graph.items():
        for d in deps:
            lines.append(f'    "{pkg}" -> "{d}";')
    lines.append("}")
    return "\n".join(lines)

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

    # Строим граф
    graph = build_dependency_graph(package_name, max_depth)

    # Генерируем DOT-код
    dot_code = generate_dot_code(graph, package_name)

    # Записываем в файл
    with open(output_file, "w") as f:
        f.write(dot_code)

    # Выводим на экран
    print(dot_code)

if __name__ == "__main__":
    main()
