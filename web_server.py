"""
Веб-сервер для проекта AgroDrones (Flask).

ЭТО СВЯЗУЮЩЕЕ ЗВЕНО между браузером и нашим Python-кодом. Важно понимать:
сервер НЕ дублирует логику — он импортирует те же самые классы (Field, дроны,
Simulation) и те же алгоритмы, что и консольная версия, и просто вызывает их
по запросу из браузера.

Как это работает (схема "клиент-сервер"):
  1. Браузер открывает http://localhost:5000 и получает HTML-страницу.
  2. Когда пользователь жмёт кнопку, JavaScript в браузере шлёт запрос
     на сервер (например, GET /api/run-day).
  3. Сервер вызывает наш Python (sim.run_day_web()), получает результат
     и отправляет его обратно в браузере в формате JSON.
  4. JavaScript рисует полученные данные (поле, маршрут дрона, итог).

Запуск:
    python web_server.py
Затем открыть в браузере: http://localhost:5000

На защите можно сказать:
"Веб-версия связана с основным проектом через Flask. Браузер по HTTP дёргает
наш Python: тот же обход сетки, та же сортировка зон, тот же маршрут. Сервер —
тонкая прослойка, бизнес-логика осталась в классах. Это архитектура
клиент-сервер: фронтенд (браузер) отделён от бэкенда (наш Python)."
"""

from flask import Flask, jsonify, send_from_directory
import os
from datetime import datetime

from models.field import Field
from models.base import Base
from models.drone import ScoutDrone, SprayDrone
from simulation import Simulation

app = Flask(__name__)

# Папка, где лежит index.html (рядом с этим файлом).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def log(msg):
    """Печатает сообщение в терминал с отметкой времени.

    Простое логирование: видно, какой запрос пришёл от браузера и что
    сделал сервер. Удобно для отладки и для демонстрации на защите
    (видно, что браузер реально дёргает наш Python).
    """
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")


def build_simulation():
    """Собирает свежую симуляцию из наших классов (как в main.py)."""
    field = Field(name="Поле №1 (пшеница)", rows=8, cols=8)
    base = Base(name="Станция Альфа")
    base.add_drone(ScoutDrone(name="Скаут-1", battery=100))
    base.add_drone(SprayDrone(name="Спрей-1", battery=250, tank=22))
    return Simulation(field, base)


# Одна симуляция на сервер, живёт между запросами (хранит день, поле, историю).
sim = build_simulation()


@app.route("/")
def index():
    """Отдаёт главную HTML-страницу."""
    log("Браузер открыл страницу (GET /)")
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/field")
def api_field():
    """Возвращает текущее состояние поля (датчики) в JSON.

    Браузер зовёт это для отрисовки карты поля без запуска дня.
    """
    data = sim.field.to_dict()
    problems = sum(1 for c in data["cells"] if c["status"] != "OK")
    log(f"Разведка поля (GET /api/field) -> проблемных участков: {problems}")
    return jsonify(data)


@app.route("/api/run-day")
def api_run_day():
    """Проводит один рабочий день (вызывает наш Python) и отдаёт результат.

    Здесь и происходит главное: sim.run_day_web() гоняет обход сетки,
    сортировку зон и построение маршрута — наш настоящий код.
    """
    log("Запрос 'прожить день' (GET /api/run-day) -> запускаю симуляцию...")
    result = sim.run_day_web(threshold=110)

    if result.get("needs_reset"):
        log("  -> бак пуст, день не засчитан. Нужен новый цикл.")
        return jsonify(result)

    # Дополняем историей облётов (тоже из нашего объекта Base).
    records = sim.base.history.to_list()
    result["history"] = [
        {"day": r.day, "total": r.total, "done": r.done} for r in records
    ]
    # Записываем день в историю (связный список на базе).
    sim.base.record_flight(result["day"], result["total_zones"], result["done"])
    log(f"  -> день {result['day']}: найдено зон {result['total_zones']}, "
        f"обработано {result['done']}, бак {result['tank']}, заряд {result['battery']}")
    return jsonify(result)


@app.route("/api/reset")
def api_reset():
    """Новый цикл: обновляет поле и заряжает дроны (наш метод симуляции)."""
    sim.refuel_and_recharge()
    log("Новый цикл (GET /api/reset) -> поле обновлено, дроны заряжены, бак полон")
    return jsonify(sim.field.to_dict())


if __name__ == "__main__":
    print("=" * 55)
    print("  AgroDrones — веб-сервер запущен")
    print("  Откройте в браузере:  http://localhost:5000")
    print("  Остановить сервер:    Ctrl + C")
    print("=" * 55)
    app.run(host="127.0.0.1", port=5000, debug=False)
