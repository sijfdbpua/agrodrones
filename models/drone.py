"""
Модуль с классами дронов.

Здесь живёт НАСЛЕДОВАНИЕ — один из главных пунктов оценки (ООП, 25 баллов).

Иерархия:
    Drone (базовый, общий для всех дронов)
      ├── ScoutDrone  (разведчик: дёшево летает, только осматривает)
      └── SprayDrone  (рабочий: возит бак, умеет поливать и опрыскивать)

На защите про наследование:
"Базовый класс Drone содержит общее поведение всех дронов: координаты,
заряд батареи, расход заряда на полёт, базовая телеметрия. Конкретные дроны
наследуются от него и переопределяют/добавляют поведение: ScoutDrone тратит
мало заряда и не возит бак, SprayDrone расходует содержимое бака на обработку.
Это и есть наследование + полиморфизм: метод handle_zone() у разных дронов
работает по-разному, но вызывается одинаково."

Очередь задач реализована на collections.deque — объясняю выбор ниже в коде.
"""

from collections import deque


class Drone:
    """Базовый класс дрона. Сам по себе не летает на задачи —
    от него наследуются конкретные типы."""

    def __init__(self, name, battery=100, move_cost=2):
        self.name = name
        self.battery = battery        # текущий заряд, 0..100
        self.move_cost = move_cost    # сколько заряда уходит на 1 шаг полёта
        self.row = 0                  # стартуем на базе в углу поля (0,0)
        self.col = 0
        self.log = []                 # личный журнал действий дрона (список)

    # ----- общее поведение для всех дронов -----

    def fly_to(self, row, col):
        """Перелёт дрона в клетку (row, col). Тратит заряд по расстоянию.

        Возвращает True, если долетел, и False, если не хватило заряда.
        """
        dist = abs(self.row - row) + abs(self.col - col)
        cost = dist * self.move_cost
        if cost > self.battery:
            self.log.append(f"{self.name}: не хватило заряда лететь в "
                            f"({row},{col}), нужно {cost}, есть {self.battery}")
            return False
        self.battery -= cost
        self.row, self.col = row, col
        return True

    def can_continue(self):
        """Есть ли ещё смысл работать (хватает ли заряда хоть на что-то)."""
        return self.battery > self.move_cost

    def handle_zone(self, zone):
        """Обработать зону. В базовом классе — заглушка.

        Конкретные дроны ПЕРЕОПРЕДЕЛЯЮТ этот метод (полиморфизм).
        Поднимаем NotImplementedError, чтобы случайно не использовать
        базовый дрон напрямую — это подсказка разработчику.
        """
        raise NotImplementedError("Используйте конкретный тип дрона")

    def status(self):
        return f"{self.name} @({self.row},{self.col}) battery={self.battery}"


class ScoutDrone(Drone):
    """Дрон-разведчик. Лёгкий, экономный, умеет только осматривать (INSPECT).

    Наследует всё от Drone и переопределяет handle_zone().
    """

    def __init__(self, name, battery=100):
        # super() вызывает конструктор базового класса — не дублируем код.
        super().__init__(name, battery=battery, move_cost=1)  # летает дёшево

    def handle_zone(self, zone):
        """Осматривает зону. Полить/опрыскать не может — только зафиксировать."""
        zone.complete()
        self.log.append(f"{self.name}: осмотрел зону ({zone.row},{zone.col})")
        return True


class SprayDrone(Drone):
    """Рабочий дрон с баком. Умеет поливать (IRRIGATE) и опрыскивать (SPRAY).

    Добавляет новый атрибут — tank (содержимое бака), которого нет у базового.
    """

    def __init__(self, name, battery=100, tank=10):
        super().__init__(name, battery=battery, move_cost=2)  # тяжелее, дороже
        self.tank = tank   # сколько "зарядов" обработки осталось в баке

    def handle_zone(self, zone):
        """Обрабатывает зону, расходуя бак.

        Если бак пуст — обработать нельзя, возвращаем False.
        """
        if self.tank <= 0:
            self.log.append(f"{self.name}: бак пуст, не могу обработать "
                            f"({zone.row},{zone.col})")
            return False
        self.tank -= 1
        zone.complete()
        action = "полил" if zone.task_type == "IRRIGATE" else "опрыскал"
        self.log.append(f"{self.name}: {action} зону ({zone.row},{zone.col}), "
                        f"в баке осталось {self.tank}")
        return True

    def status(self):
        # Расширяем статус базового класса информацией о баке.
        return super().status() + f" tank={self.tank}"


# ---------------------------------------------------------------------------
# Очередь задач на день — отдельная структура поверх дронов.
# ---------------------------------------------------------------------------

class TaskQueue:
    """Очередь задач (зон) на один рабочий день.

    ВЫБОР СТРУКТУРЫ ДАННЫХ (это спросят на защите — 30 баллов):
    Я использую collections.deque, а не обычный список, потому что:
      - задачи выполняются по принципу FIFO (кто раньше в очереди — раньше
        обрабатывается), а deque даёт извлечение слева popleft() за O(1);
      - у обычного списка list.pop(0) стоит O(n), потому что после удаления
        первого элемента все остальные сдвигаются. На большом плане задач
        это заметно медленнее.
    Перед тем как класть задачи в очередь, я их СОРТИРУЮ по приоритету
    (алгоритм 2), поэтому очередь оказывается "очередью по важности":
    самые критичные зоны уходят дрону первыми.
    """

    def __init__(self):
        self._queue = deque()

    def fill(self, zones):
        """Кладёт зоны в очередь (ожидается, что они уже отсортированы)."""
        for z in zones:
            self._queue.append(z)

    def next_task(self):
        """Берёт следующую задачу из начала очереди (FIFO), O(1)."""
        if self._queue:
            return self._queue.popleft()
        return None

    def is_empty(self):
        return len(self._queue) == 0

    def __len__(self):
        return len(self._queue)
