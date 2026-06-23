"""
Модуль с классом Field (поле).

Поле — прямоугольная сетка клеток. В каждой клетке находится Sensor.
Класс Field отвечает за генерацию датчиков, обход сетки, поиск проблемных зон,
отрисовку карты в консоли и передачу данных веб-интерфейсу.

На защите это удобно объяснять так:
"Поле хранится как двумерный список объектов Sensor. Это естественная
структура для карты: доступ к клетке идёт за O(1), а обход всей сетки —
обычный вложенный цикл за O(rows * cols)."
"""

import random

from models.sensor import Sensor
from models.zone import Zone


class Field:
    """Поле как сетка датчиков размером rows x cols."""

    def __init__(self, name, rows, cols):
        self.name = name
        self.rows = rows
        self.cols = cols
        self.grid = []
        self._generate_sensors()

    def _generate_sensors(self):
        """Создаёт новую сетку виртуальных датчиков."""
        self.grid = []
        for r in range(self.rows):
            row_sensors = []
            for c in range(self.cols):
                moisture = random.randint(10, 90)
                health = random.randint(30, 100)
                pest = random.randint(0, 60)
                row_sensors.append(Sensor(r, c, moisture, health, pest))
            self.grid.append(row_sensors)

    def scan_for_problems(self, threshold=70):
        """АЛГОРИТМ 1: обход сетки и сбор проблемных зон.

        Сложность: O(rows * cols), потому что каждая клетка проверяется ровно
        один раз. Для карты поля это оптимальный и понятный подход.
        """
        zones = []
        for r in range(self.rows):
            for c in range(self.cols):
                sensor = self.grid[r][c]
                score = sensor.problem_score()
                if score >= threshold:
                    task = self._decide_task(sensor)
                    zones.append(Zone(r, c, score, task))
        return zones

    def _decide_task(self, sensor):
        """Выбирает тип обработки по показаниям датчика."""
        if sensor.pest_level >= 35:
            return "SPRAY"
        if sensor.moisture < 40:
            return "IRRIGATE"
        return "INSPECT"

    def treat_zone(self, row, col, task_type):
        """Применяет результат обработки к реальному датчику поля."""
        self.grid[row][col].apply_treatment(task_type)

    def render(self):
        """Рисует карту поля символами для консольной версии."""
        lines = []
        header = "    " + " ".join(f"{c:2}" for c in range(self.cols))
        lines.append(header)
        for r in range(self.rows):
            row_syms = " ".join(f" {self.grid[r][c].symbol()}" for c in range(self.cols))
            lines.append(f"{r:2}  {row_syms}")
        lines.append("")
        lines.append("Легенда:  . — OK    ! — WARNING    # — CRITICAL")
        return "\n".join(lines)

    def count_problem_cells(self):
        """Считает количество клеток, которые требуют внимания."""
        total = 0
        for row in self.grid:
            for sensor in row:
                if sensor.status() != "OK":
                    total += 1
        return total

    def to_dict(self):
        """Возвращает состояние поля в формате, удобном для JSON."""
        cells = []
        for r in range(self.rows):
            for c in range(self.cols):
                cells.append(self.grid[r][c].to_dict())
        return {
            "name": self.name,
            "rows": self.rows,
            "cols": self.cols,
            "problem_cells": self.count_problem_cells(),
            "cells": cells,
        }
