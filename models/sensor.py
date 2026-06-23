"""
Модуль с классом Sensor (датчик).

Датчик — источник данных в системе AgroDrones. Он хранит показания одной
клетки поля: влажность почвы, здоровье растений и уровень вредителей.

Ключевая идея ООП здесь — инкапсуляция: данные и логика их оценки находятся
в одном объекте. Поэтому Sensor не просто хранит числа, а сам умеет:
  • рассчитать балл проблемности;
  • определить статус клетки;
  • обновить показатели после обработки дроном.
"""


class Sensor:
    """Виртуальный датчик в одной клетке поля."""

    def __init__(self, row, col, moisture, health, pest_level):
        self.row = row
        self.col = col
        self.moisture = moisture
        self.health = health
        self.pest_level = pest_level

    def problem_score(self):
        """Считает балл проблемности клетки.

        Чем выше балл, тем хуже состояние участка и тем выше приоритет
        обработки. Формула специально простая, чтобы её было легко объяснить
        на защите:
          • засуха увеличивает балл;
          • плохое здоровье растений увеличивает балл;
          • вредители имеют повышенный вес, потому что быстро распространяются.
        """
        score = 0
        if self.moisture < 40:
            score += 40 - self.moisture
        score += 100 - self.health
        score += self.pest_level * 1.5
        return round(score, 1)

    def status(self):
        """Возвращает состояние клетки: OK, WARNING или CRITICAL."""
        score = self.problem_score()
        if score >= 120:
            return "CRITICAL"
        if score >= 70:
            return "WARNING"
        return "OK"

    def symbol(self):
        """Один символ для консольной карты поля."""
        return {"CRITICAL": "#", "WARNING": "!", "OK": "."}[self.status()]

    def apply_treatment(self, task_type):
        """Изменяет показатели клетки после обработки дроном.

        Это делает симуляцию честнее: обработанная зона не просто отмечается
        галочкой в интерфейсе, а реально становится здоровее в данных поля.
        """
        if task_type == "SPRAY":
            self.pest_level = max(0, self.pest_level - 45)
            self.health = min(100, self.health + 12)
        elif task_type == "IRRIGATE":
            self.moisture = min(90, self.moisture + 35)
            self.health = min(100, self.health + 8)
        else:
            self.health = min(100, self.health + 4)

    def to_dict(self):
        """Готовит данные датчика для JSON-ответа веб-сервера."""
        return {
            "row": self.row,
            "col": self.col,
            "moisture": self.moisture,
            "health": self.health,
            "pest_level": self.pest_level,
            "score": self.problem_score(),
            "status": self.status(),
        }

    def __repr__(self):
        return f"Sensor({self.row},{self.col}, score={self.problem_score()})"
