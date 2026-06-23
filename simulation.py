"""
Модуль с движком симуляции (Simulation).

Это "мозг" приложения, который связывает все объекты вместе и проводит
один рабочий день агрохозяйства по шагам:

    1. Дрон-разведчик облетает поле и собирает проблемные зоны (обход сетки).
    2. Зоны сортируются по приоритету (merge sort).
    3. Строится маршрут облёта (жадный поиск ближайшей зоны).
    4. Рабочий дрон летит по маршруту и обрабатывает зоны, пока хватает
       заряда и содержимого бака.
    5. Итог дня записывается в историю (связный список на базе).

На защите это удобно показывать как "сценарий использования": один вызов
run_day() — и видно весь конвейер от данных к действию.
"""

from models.drone import TaskQueue
from algorithms import merge_sort_zones, build_route


class Simulation:
    """Управляет полем, базой и ходом времени (днями)."""

    def __init__(self, field, base):
        self.field = field
        self.base = base
        self.day = 0

    def _get_scout(self):
        """Находит во флоте дрон-разведчик (по имени класса)."""
        from models.drone import ScoutDrone
        for d in self.base.drones:
            if isinstance(d, ScoutDrone):
                return d
        return None

    def _get_worker(self):
        """Находит во флоте рабочий дрон с баком."""
        from models.drone import SprayDrone
        for d in self.base.drones:
            if isinstance(d, SprayDrone):
                return d
        return None

    def run_day(self, threshold=70, verbose=True):
        """Проводит один полный рабочий день. Возвращает текстовый отчёт."""
        self.day += 1
        report = [f"\n========== ДЕНЬ {self.day} =========="]

        scout = self._get_scout()
        worker = self._get_worker()
        if scout is None or worker is None:
            return "Ошибка: во флоте должен быть и разведчик, и рабочий дрон."

        # Шаг 1: разведка — обход сетки поля (АЛГОРИТМ 1 внутри field).
        zones = self.field.scan_for_problems(threshold=threshold)
        report.append(f"[Разведка] {scout.name} облетел поле, "
                    f"найдено проблемных зон: {len(zones)}")

        if not zones:
            report.append("Поле в порядке, обработка не требуется.")
            self.base.record_flight(self.day, 0, 0)
            return "\n".join(report)

        # Шаг 2: сортировка зон по приоритету (АЛГОРИТМ 2 — merge sort).
        zones = merge_sort_zones(zones)
        top = zones[0]
        report.append(f"[Приоритеты] Самая критичная зона: ({top.row},{top.col}) "
                    f"приоритет {top.priority}, действие {top.task_type}")

        # Шаг 3: маршрут облёта (АЛГОРИТМ 3 — жадный поиск ближайшей).
        # Важно: маршрут строим от базы, но сохраняем приоритетный порядок
        # как основу — здесь для наглядности облетаем по ближайшему пути.
        route = build_route(zones, worker.row, worker.col)
        report.append(f"[Маршрут] Построен маршрут облёта из {len(route)} точек "
                    f"(жадный поиск ближайшей зоны).")

        # Складываем зоны в очередь задач (FIFO на deque).
        queue = TaskQueue()
        queue.fill(route)

        # Шаг 4: рабочий дрон выполняет задачи из очереди.
        done = 0
        while not queue.is_empty() and worker.can_continue():
            task = queue.next_task()         # берём из начала очереди, O(1)
            if not worker.fly_to(task.row, task.col):
                report.append("  Заряд кончился в пути — день завершён досрочно.")
                break
            ok = worker.handle_zone(task)     # полиморфный вызов
            if ok:
                done += 1
            elif worker.tank <= 0:
                report.append("  Бак пуст — возвращаемся на базу.")
                break

        report.append(f"[Итог] Обработано зон: {done} из {len(route)}")
        report.append(f"       {worker.status()}")
        if done == 0:
            report.append("       (!) Дрон не смог обработать зоны. "
                        "Выполните 'Новый цикл' (пункт 5), чтобы зарядить "
                        "батареи и наполнить бак.")

        # Шаг 5: записываем день в историю (связный список).
        self.base.record_flight(self.day, len(route), done)

        # По желанию печатаем подробный журнал рабочего дрона.
        if verbose and worker.log:
            report.append("  Журнал дрона:")
            for line in worker.log[-done:] if done else []:
                report.append(f"    {line}")

        return "\n".join(report)

    def refuel_and_recharge(self):
        """Заправляет баки и заряжает батареи всех дронов (новый день/сервис)."""
        from models.drone import SprayDrone
        for d in self.base.drones:
            d.row, d.col = 0, 0       # дроны вернулись на базу
            d.log.clear()
            if isinstance(d, SprayDrone):
                d.battery = 250       # рабочему нужен большой запас на облёт
                d.tank = 22
            else:
                d.battery = 100       # разведчику хватает меньше
        # Перегенерируем показания поля — имитируем, что прошло время.
        self.field._generate_sensors()

    # -----------------------------------------------------------------
    # Веб-версия: проводит день и возвращает данные для анимации в браузере.
    # -----------------------------------------------------------------
    def run_day_web(self, threshold=110):
        """Как run_day(), но вместо текста возвращает словарь с данными.

        Браузер по этим данным рисует анимацию: какие зоны найдены, в каком
        порядке дрон их облетает, какие успел обработать. Вся логика
        (обход сетки, сортировка по приоритету, расход бака) — та же, что в
        консольной версии: мы переиспользуем те же алгоритмы и классы.

        Облёт идёт ПО ПРИОРИТЕТУ: дрон сначала летит к самым критичным зонам
        (с наибольшим баллом проблемности), потом к менее важным. Так на карте
        видно, что в первую очередь обрабатываются красные участки.
        """
        from algorithms import merge_sort_zones
        worker = self._get_worker()

        # Шаг 1: обход сетки — поиск проблемных зон (тот же метод поля).
        zones = self.field.scan_for_problems(threshold=threshold)
        # Шаг 2: сортировка по приоритету (тот же merge sort) — критичные первыми.
        route = merge_sort_zones(zones)

        # Если обрабатывать нечего (бак пуст) — день НЕ засчитываем,
        # сообщаем браузеру, что нужен новый цикл.
        if worker.tank <= 0:
            return {
                "day": self.day,
                "needs_reset": True,
                "total_zones": len(route),
                "done": 0,
                "battery": worker.battery,
                "tank": worker.tank,
                "steps": [],
                "field": self.field.to_dict(),
            }

        self.day += 1

        # Шаг 3: облёт строго по приоритету (route уже отсортирован).
        worker.row, worker.col = 0, 0
        steps = []
        done = 0
        treated = set()     # координаты обработанных зон (станут зелёными)
        for z in route:
            dist = abs(worker.row - z.row) + abs(worker.col - z.col)
            cost = dist * worker.move_cost
            if cost > worker.battery:
                steps.append({"row": z.row, "col": z.col,
                              "task": z.task_type, "done": False})
                break
            worker.battery -= cost
            worker.row, worker.col = z.row, z.col
            if worker.tank <= 0:
                steps.append({"row": z.row, "col": z.col,
                              "task": z.task_type, "done": False})
                break
            worker.tank -= 1
            done += 1
            treated.add((z.row, z.col))
            steps.append({"row": z.row, "col": z.col,
                          "task": z.task_type, "done": True})

        # Готовим состояние поля: обработанные зоны помечаем как вылеченные (OK).
        field_data = self.field.to_dict()
        for cell in field_data["cells"]:
            if (cell["row"], cell["col"]) in treated:
                cell["status"] = "OK"      # дрон обработал — участок здоров
                cell["treated"] = True     # пометка для галочки в браузере

        return {
            "day": self.day,
            "needs_reset": False,
            "total_zones": len(route),
            "done": done,
            "battery": worker.battery,
            "tank": worker.tank,
            "steps": steps,
            "field": field_data,
        }
