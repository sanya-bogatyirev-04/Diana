import requests
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import json
from urllib.parse import quote

@dataclass
class Material:
    name: str
    length: float  # м
    width: float   # м
    height: float  # м
    gost: str
    mortar_rate: float = 0.23  # норма расхода раствора м3/м3

@dataclass
class Wall:
    length: float  # Длина стены (м)
    height: float  # Высота стены (м)
    width: float   # Толщина стены (м)

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

def input_with_back(prompt: str, input_type: type = str, min_val=None):
    """Функция ввода с возможностью возврата по клавише 'w'"""
    while True:
        try:
            print("\nНажмите 'w' для возврата назад")
            value = input(prompt)
            
            if value.lower() == 'w':
                return None
                
            if input_type == float:
                value = float(value)
            elif input_type == int:
                value = int(value)
                
            if min_val is not None and value < min_val:
                print(f"Значение должно быть не менее {min_val}")
                continue
                
            return value
            
        except ValueError:
            print(f"Пожалуйста, введите корректное значение типа {input_type.__name__}")

def calculate_wall_volume(walls: List[Wall], material_width: float) -> Tuple[float, float]:
    """Расчет объема стен с учетом ширины материала"""
    if not walls:
        return 0.0, 0.0
    
    # Для прямоугольных зданий
    if len(walls) == 4:
        unique_lengths = {wall.length for wall in walls}
        if len(unique_lengths) == 2:
            a, b = sorted(unique_lengths)
            perimeter = 2 * (a + b)
            avg_height = sum(wall.height for wall in walls) / 4
            width_layers = sum(wall.width for wall in walls) / (4 * material_width)
            return perimeter * avg_height * material_width * width_layers, perimeter
    
    # Для произвольных конфигураций
    total_area = sum(wall.length * wall.height for wall in walls)
    width_layers = sum(wall.width for wall in walls) / (len(walls) * material_width)
    perimeter = sum(wall.length for wall in walls)
    return total_area * material_width * width_layers, perimeter

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
            
            length = input_with_back("Длина стены (м): ", float, 0.1)
            if length is None:
                if walls:
                    walls.pop()
                    continue
                print("Нет стен для удаления")
                continue
            
            height = input_with_back("Высота стены (м): ", float, 0.1)
            if height is None:
                if walls:
                    walls.pop()
                    continue
                print("Нет стен для удаления")
                continue
            
            width = input_with_back("Толщина стены (м): ", float, 0.05)
            if width is None:
                if walls:
                    walls.pop()
                    continue
                print("Нет стен для удаления")
                continue
            
            walls.append(Wall(length, height, width))

            if len(walls) >= 4 and input("Добавить еще стену? (y/n): ").lower() != 'y':
                break
            elif len(walls) < 4 and input("Добавить следующую стену? (y/n): ").lower() != 'y':
                if len(walls) < 2:
                    print("Минимальное количество стен - 2")
                    continue
                break

        while True:
            # Выбор материала
            print("\nДоступные материалы:")
            for i, (key, mat) in enumerate(materials.items(), 1):
                print(f"{i}. {mat.name} ({mat.gost}) - {mat.length}x{mat.width}x{mat.height} м")

            print("n. Добавить новый материал")
            print("q. Завершить расчеты")
            choice = input("Выберите материал (введите номер, название или команду): ").strip().lower()

            if choice == 'q':
                break
            elif choice == 'n':
                name = input("Название материала: ").strip()
                length = input_with_back("Длина материала (м): ", float, 0.01)
                width = input_with_back("Ширина материала (м): ", float, 0.01)
                height = input_with_back("Высота материала (м): ", float, 0.01)
                gost = input("Номер ГОСТ (например, 'ГОСТ 530-2012'): ").strip()

                gost_info = GOSTLoader.load_gost_info(gost)
                if gost_info:
                    print(f"Найдена информация о ГОСТ: {gost_info.get('title', '')}")

                mortar_rate = input_with_back("Норма расхода раствора (м3/м3 кладки): ", float, 0.0)
                material = Material(name, length, width, height, gost, mortar_rate)
                materials[name.lower()] = material
                save_materials_to_file(materials)
                continue
            elif choice.isdigit():
                material = list(materials.values())[int(choice) - 1]
            else:
                material = materials.get(choice)
                if not material:
                    print("Материал не найден, попробуйте снова")
                    continue

            print(f"\nВыбран материал: {material.name} {material.length}x{material.width}x{material.height} м")

            # Расчет объема стен
            total_wall_volume, perimeter = calculate_wall_volume(walls, material.width)

            # Ввод данных о проемах
            openings = []
            print("\nВвод данных о проемах (окна, двери и др.)")
            while True:
                name = input("\nТип проема (например, 'окно', 'дверь'): ").strip()
                if not name:
                    break

                length = input_with_back("Длина проема (м): ", float, 0.1)
                if length is None:
                    if openings:
                        openings.pop()
                        continue
                    print("Нет проемов для удаления")
                    continue
                
                height = input_with_back("Высота проема (м): ", float, 0.1)
                if height is None:
                    if openings:
                        openings.pop()
                        continue
                    print("Нет проемов для удаления")
                    continue
                
                count = input_with_back("Количество таких проемов: ", int, 1)
                if count is None:
                    if openings:
                        openings.pop()
                        continue
                    print("Нет проемов для удаления")
                    continue
                
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

            net_wall_volume = max(0, total_wall_volume - total_openings_volume)

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
            print(f"Материал: {material.name}")
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
            with open("calculation_results.txt", "a", encoding="utf-8") as f:
                f.write("\nРезультаты расчета материалов\n")
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
            input("Нажмите Enter чтобы продолжить...")

    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")

if __name__ == "__main__":
    calculate_materials()