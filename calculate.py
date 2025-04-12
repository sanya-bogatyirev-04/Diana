import requests
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import json
from urllib.parse import quote


@dataclass
class Material:
    name: str
    length: float  # м
    width: float  # м
    height: float  # м
    gost: str
    mortar_rate: float = 0.23  # норма расхода раствора м3/м3


@dataclass
class Wall:
    length: float  # Длина стены (м)
    height: float  # Высота стены (м)
    width: float  # Толщина стены (м)


@dataclass
class Opening:
    name: str
    length: float
    height: float
    count: int = 1
    width: Optional[float] = None


class GOSTLoader:
    GOST_API_URL = "https://gost-api.example.com/search"

    @classmethod
    def load_gost_info(cls, gost_number: str) -> Optional[dict]:
        try:
            response = requests.get(f"{cls.GOST_API_URL}?query={quote(gost_number)}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None


def load_materials_from_file(filename: str = "materials.json") -> Dict[str, Material]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {k: Material(**v) for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_materials_to_file(materials: Dict[str, Material], filename: str = "materials.json"):
    data = {k: vars(v) for k, v in materials.items()}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def input_float(prompt: str, min_val: float = 0.0) -> float:
    while True:
        try:
            value = float(input(prompt))
            if value >= min_val:
                return value
            print(f"Значение должно быть не менее {min_val}")
        except ValueError:
            print("Пожалуйста, введите число")


def input_int(prompt: str, min_val: int = 0) -> int:
    while True:
        try:
            value = int(input(prompt))
            if value >= min_val:
                return value
            print(f"Значение должно быть не менее {min_val}")
        except ValueError:
            print("Пожалуйста, введите целое число")


def calculate_wall_volume(walls: List[Wall]) -> Tuple[float, float]:
    """
    Правильный расчет объема стен
    Возвращает: (общий объем стен, периметр)
    """
    if not walls:
        return 0.0, 0.0

    # Для прямоугольных зданий (4 стены: 2 пары одинаковых)
    if len(walls) == 4:
        unique_lengths = {wall.length for wall in walls}
        if len(unique_lengths) == 2:
            a, b = sorted(unique_lengths)
            perimeter = 2 * (a + b)
            avg_height = sum(wall.height for wall in walls) / 4
            avg_width = sum(wall.width for wall in walls) / 4
            return perimeter * avg_height * avg_width, perimeter

    # Для произвольных конфигураций
    total_area = sum(wall.length * wall.height for wall in walls)
    avg_width = sum(wall.width for wall in walls) / len(walls)
    perimeter = sum(wall.length for wall in walls)
    return total_area * avg_width, perimeter


def calculate_materials():
    print("Расчет кладочных материалов и раствора для стен дома")
    print("-----------------------------------------------------")

    materials = load_materials_from_file()
    if not materials:
        materials = {
            "кирпич": Material(
                name="Кирпич керамический",
                length=0.25,
                width=0.12,
                height=0.065,
                gost="ГОСТ 530-2012"
            ),
            "блок": Material(
                name="Блок керамический",
                length=0.51,
                width=0.25,
                height=0.219,
                gost="ГОСТ 530-2012"
            )
        }
        save_materials_to_file(materials)

    try:
        # Ввод параметров стен
        walls = []
        print("\nВвод параметров стен (длина, высота, толщина)")
        print("Для прямоугольного дома введите 4 стены (2 пары противоположных)")
        

        while True:
            print(f"\nСтена #{len(walls) + 1}:")
            length = input_float("Длина стены (м): ")
            height = input_float("Высота стены (м): ")
            width = input_float("Толщина стены (м): ")
            walls.append(Wall(length, height, width))

            if len(walls) >= 4 and input("Добавить еще стену? (y/n): ").lower() != 'y':
                break
            elif len(walls) < 4 and input("Добавить следующую стену? (y/n): ").lower() != 'y':
                if len(walls) < 2:
                    print("Минимальное количество стен - 2")
                    continue
                break

        # Расчет объема стен
        total_wall_volume, perimeter = calculate_wall_volume(walls)

        # Выбор материала
        print("\nДоступные материалы:")
        for i, (key, mat) in enumerate(materials.items(), 1):
            print(f"{i}. {mat.name} ({mat.gost}) - {mat.length}x{mat.width}x{mat.height} м")

        print("n. Добавить новый материал")
        choice = input("Выберите материал (введите номер или название): ").strip().lower()

        if choice == 'n':
            name = input("Название материала: ").strip()
            length = input_float("Длина материала (м): ")
            width = input_float("Ширина материала (м): ")
            height = input_float("Высота материала (м): ")
            gost = input("Номер ГОСТ (например, 'ГОСТ 530-2012'): ").strip()

            gost_info = GOSTLoader.load_gost_info(gost)
            if gost_info:
                print(f"Найдена информация о ГОСТ: {gost_info.get('title', '')}")

            mortar_rate = input_float("Норма расхода раствора (м3/м3 кладки): ", 0.0)
            material = Material(name, length, width, height, gost, mortar_rate)
            materials[name.lower()] = material
            save_materials_to_file(materials)
        elif choice.isdigit():
            material = list(materials.values())[int(choice) - 1]
        else:
            material = materials.get(choice, materials["кирпич"])

        print(f"\nВыбран материал: {material.name} {material.length}x{material.width}x{material.height} м")

        # Ввод данных о проемах
        openings = []
        print("\nВвод данных о проемах (окна, двери и др.)")
        while True:
            name = input("\nТип проема (например, 'окно', 'дверь'): ").strip()
            if not name:
                break

            length = input_float("Длина проема (м): ")
            height = input_float("Высота проема (м): ")
            count = input_int("Количество таких проемов: ", 1)

            custom_width = input("Ширина проема (м, оставьте пустым для использования ширины стены): ").strip()
            width = float(custom_width) if custom_width else None

            openings.append(Opening(name, length, height, count, width))

        # Расчет объемов проемов
        total_openings_volume = 0
        opening_details = []

        avg_wall_width = sum(wall.width for wall in walls) / len(walls) if walls else 0
        for op in openings:
            op_width = op.width if op.width is not None else avg_wall_width
            volume = op.length * op.height * op_width * op.count
            total_openings_volume += volume
            opening_details.append((op.name, volume))

        net_wall_volume = max(0, total_wall_volume - total_openings_volume)  # Не может быть отрицательным

        # Расчет количества материалов
        block_volume = material.length * material.width * material.height
        blocks_count = net_wall_volume / block_volume if block_volume > 0 else 0

        # Расчет раствора
        mortar_volume = net_wall_volume * material.mortar_rate
        

        # Расчет количества в стенах
        blocks_in_walls = []
        for i, wall in enumerate(walls, 1):
            length_blocks = max(1, round(wall.length / material.length))
            height_blocks = max(1, round(wall.height / material.height))
            width_blocks = max(1, round(wall.width / material.width))
            blocks_in_wall = length_blocks * height_blocks * width_blocks
            blocks_in_walls.append((i, blocks_in_wall))

        # Вывод результатов
        print("\nРезультаты расчета:")
        print("-------------------")
        print(f"Общее количество стен: {len(walls)}")
        print(f"Общий периметр: {perimeter:.2f} м")
        print(f"Общий объем стен: {total_wall_volume:.2f} м3")

        if openings:
            print(f"\nОбщий объем проемов: {total_openings_volume:.2f} м3")
            print("Детализация проемов:")
            for name, vol in opening_details:
                print(f"- {name}: {vol:.2f} м3")

        print(f"\nЧистый объем кладки: {net_wall_volume:.2f} м3")
        print(f"\nКоличество {material.name.lower()}: {round(blocks_count)} шт (+5-10% запас)")

        print("\nКоличество материала по стенам:")
        for i, count in blocks_in_walls:
            print(f"- Стена #{i}: {count} шт")

        print(f"\nОбъем раствора (по {material.gost}): {mortar_volume:.2f} м3")

        # Сохранение результатов
        with open("calculation_results.txt", "w", encoding="utf-8") as f:
            f.write("Результаты расчета материалов\n")
            f.write("=============================\n\n")
            f.write(f"Материал: {material.name} ({material.gost})\n")
            f.write(f"Размеры: {material.length}x{material.width}x{material.height} м\n\n")
            f.write(f"Общий объем кладки: {net_wall_volume:.2f} м3\n")
            f.write(f"Количество материала: {round(blocks_count)} шт (+5-10% запас)\n")
            f.write(f"Объем раствора: {mortar_volume:.2f} м3\n\n")

            f.write("Детализация по стенам:\n")
            for i, count in blocks_in_walls:
                f.write(f"- Стена #{i}: {count} шт\n")

        print("\nРезультаты сохранены в файл 'calculation_results.txt'")

    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")


if __name__ == "__main__":
    calculate_materials()

