from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Record
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Замените на свой секрет

# Настройка подключения к PostgreSQL
DB_USER = "testuser"
DB_PASS = "testpassword"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "testdb"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)  # Автоматическое создание таблиц при запуске

Session = sessionmaker(bind=engine)

DATE_FORMAT = "%Y-%m-%d_%H:%M"


@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "jsonfile" not in request.files:
            flash("Файл не загружен")
            return redirect(request.url)

        file = request.files["jsonfile"]
        if file.filename == "":
            flash("Файл не выбран")
            return redirect(request.url)

        try:
            data = json.load(file)
        except Exception:
            flash("Ошибка разбора JSON")
            return redirect(request.url)

        if not isinstance(data, list):
            flash("JSON должен быть массивом объектов")
            return redirect(request.url)

        session = Session()
        errors = []
        for idx, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                errors.append(f"Элемент #{idx} не объект")
                continue

            name = item.get("name")
            date_str = item.get("date")

            if name is None or date_str is None:
                errors.append(f"Элемент #{idx}: отсутствуют ключи 'name' или 'date'")
                continue

            if not isinstance(name, str) or len(name) >= 50:
                errors.append(f"Элемент #{idx}: 'name' должно быть строкой менее 50 символов")
                continue

            try:
                date_obj = datetime.strptime(date_str, DATE_FORMAT)
            except ValueError:
                errors.append(f"Элемент #{idx}: неправильный формат 'date', ожидается YYYY-MM-DD_HH:mm")
                continue

            record = Record(name=name, date=date_obj)
            session.add(record)

        if errors:
            session.rollback()
            for err in errors:
                flash(err)
            return redirect(request.url)
        else:
            session.commit()
            flash(f"Успешно добавлено {len(data)} записей")
            return redirect(url_for("show_records"))

    return render_template("upload.html")


@app.route("/records")
def show_records():
    session = Session()
    records = session.query(Record).all()
    session.close()
    return render_template("records.html", records=records)


if __name__ == "__main__":
    # Запуск на localhost:5000
    app.run(host="127.0.0.1", port=5000, debug=True)

