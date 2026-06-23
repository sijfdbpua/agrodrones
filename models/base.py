"""
Модуль с классом Base (база дронов) и простым связным списком истории.

База — это "дом" дронов и склад данных о проведённых облётах.
Здесь я специально реализую СВЯЗНЫЙ СПИСОК вручную (а не беру готовый list),
чтобы продемонстрировать понимание структур данных — в задании прямо
просят "связный список для хранения истории обработок".

На защите:
"Историю облётов поля я храню в односвязном списке собственной реализации.
Связный список хорош, когда мы постоянно добавляем записи в начало за O(1)
и не нуждаемся в произвольном доступе по индексу — нам важен только порядок
'от свежих к старым' и проход по всей истории. Каждая запись (Node) хранит
данные и ссылку на предыдущую запись."
"""


class HistoryNode:
    """Один узел связного списка — запись об одном облёте."""

    def __init__(self, day, total, done):
        self.day = day            # номер дня симуляции
        self.total = total        # сколько зон было найдено
        self.done = done          # сколько зон успели обработать
        self.next = None          # ссылка на следующий узел (более старый)


class FlightHistory:
    """Односвязный список записей об облётах. Новые записи — в начало."""

    def __init__(self):
        self.head = None   # ссылка на самую свежую запись
        self.size = 0

    def add(self, day, total, done):
        """Добавляет запись в начало списка за O(1)."""
        node = HistoryNode(day, total, done)
        node.next = self.head   # новая запись ссылается на бывшую первую
        self.head = node        # и сама становится первой
        self.size += 1

    def to_list(self):
        """Проходит по всему списку и собирает записи в обычный список.

        Нужно для вывода истории на экран. Проход — O(n).
        """
        result = []
        current = self.head
        while current is not None:
            result.append(current)
            current = current.next
        return result


class Base:
    """База дронов: хранит флот дронов и историю облётов поля."""

    def __init__(self, name):
        self.name = name
        self.drones = []                 # список дронов (флот)
        self.history = FlightHistory()   # связный список облётов

    def add_drone(self, drone):
        self.drones.append(drone)

    def record_flight(self, day, total, done):
        """Записывает итог рабочего дня в историю."""
        self.history.add(day, total, done)

    def show_history(self):
        """Возвращает текст с историей облётов (от свежих к старым)."""
        records = self.history.to_list()
        if not records:
            return "История пуста — облётов ещё не было."
        lines = ["История облётов (свежие сверху):"]
        for rec in records:
            lines.append(f"  День {rec.day}: найдено зон {rec.total}, "
                        f"обработано {rec.done}")
        return "\n".join(lines)
