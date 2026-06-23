"""
Модуль с классом Field (поле).

Поле — это прямоугольная СЕТКА клеток, в каждой клетке сидит датчик (Sensor).
Field хранит эту сетку и умеет:
  1) сгенерировать случайные показания датчиков (имитация реальности);
  2) обойти всю сетку и собрать проблемные клетки (АЛГОРИТМ 1 — обход сетки);
  3) нарисовать карту поля в консоли.

На защите про структуру данных:
"Поле я храню как двумерный список (список списков) объектов Sensor.
Двумерный список — естественная структура для сетки/матрицы: доступ к
любой клетке за O(1) по индексам [row][col], и его легко обходить
вложенным циклом. Это классический выбор для представления карты/грида."
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
        # grid — двумерный список: grid[r][c] это Sensor в клетке (r, c).
        self.grid = []
        self._generate_sensors()

    def _generate_sensors(self):
        """Заполняет сетку датчиками со случайными показаниями.

        Это имитация: как будто дрон ещё не летал, но датчики уже
        что-то намеряли. Подчёркнутое имя метода (_generate_sensors)
        по соглашению PEP8 означает "внутренний, не для внешнего вызова".
        """
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
        """АЛГОРИТМ 1: обход сетки поля и сбор проблемных зон.

        Дрон последовательно облетает каждую клетку (вложенный цикл по
        строкам и столбцам — это и есть обход двумерной структуры) и
        проверяет балл проблемности датчика. Если балл выше порога —
        формируем задачу Zone и решаем, что именно делать.

        Возвращает список объектов Zone (ещё не отсортированный).

        Сложность: O(rows * cols) — мы заходим в каждую клетку ровно один
        раз. Для сетки это оптимально: меньше, чем все клетки, обойти нельзя.
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
        """Решает, какой тип обработки нужен клетке, по её показаниям.

        Приоритет решения:
          - если много вредителей -> опрыскивание (SPRAY);
          - иначе если сухо -> полив (IRRIGATE);
          - иначе -> осмотр (INSPECT).
        """
        if sensor.pest_level >= 35:
            return "SPRAY"
        elif sensor.moisture < 40:
            return "IRRIGATE"
        else:
            return "INSPECT"

    def render(self):
        """Рисует карту поля символами (. ! #) и легенду.

        Это для наглядной демонстрации на защите: видно, где у поля
        проблемы, ещё до запуска обработки.
        """
        lines = []
        header = "    " + " ".join(f"{c:2}" for c in range(self.cols))
        lines.append(header)
        for r in range(self.rows):
            row_syms = " ".join(f" {self.grid[r][c].symbol()}"
                                for c in range(self.cols))
            lines.append(f"{r:2}  {row_syms}")
        lines.append("")
        lines.append("Легенда:  . — OK    ! — WARNING    # — CRITICAL")
        return "\n".join(lines)

    def to_dict(self):
        """Отдаёт состояние поля как словарь — для передачи в браузер (JSON).

        Этот метод нужен только для веб-версии: Flask-сервер вызывает его,
        чтобы превратить объекты Sensor в простые данные, которые умеет
        отправить по сети. Сама логика поля не меняется.
        """
        cells = []
        for r in range(self.rows):
            for c in range(self.cols):
                s = self.grid[r][c]
                cells.append({
                    "row": r,
                    "col": c,
                    "status": s.status(),       # OK / WARNING / CRITICAL
                    "score": s.problem_score(),
                })
        return {"rows": self.rows, "cols": self.cols, "cells": cells}
