from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Record
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Можно заменить на свой секретный ключ

# Настройка подключения к PostgreSQL, т.к. все равно используем на localhost, то можно указывать и здесь
DB_USER = "testuser"
DB_PASS = "testpassword"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "testdb"


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создание таблиц при запуске
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

DATE_FORMAT = "%Y-%m-%d_%H:%M"


@app.route("/", methods=["GET", "POST"])
def upload():
    success_message = None
    if request.method == "POST":
        if "jsonfile" not in request.files:
            flash("Файл не загружен", "danger")
            return redirect(request.url)

        file = request.files["jsonfile"]
        if file.filename == "":
            flash("Файл не выбран", "danger")
            return redirect(request.url)

        try:
            data = json.load(file)
        except Exception:
            flash("Ошибка разбора JSON", "danger")
            return redirect(request.url)

        if not isinstance(data, list):
            flash("JSON должен быть массивом объектов", "danger")
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
                errors.append(
                    f"Элемент #{idx}: 'name' должно быть строкой менее 50 символов"
                )
                continue

            try:
                date_obj = datetime.strptime(date_str, DATE_FORMAT)
            except ValueError:
                errors.append(
                    f"Элемент #{idx}: неправильный формат 'date', ожидается YYYY-MM-DD_HH:mm"
                )
                continue

            record = Record(name=name, date=date_obj)
            session.add(record)

        if errors:
            session.rollback()
            for err in errors:
                flash(err, "danger")
        else:
            session.commit()
            success_message = f"Успешно добавлено {len(data)} записей"

    return render_template("upload.html", success_message=success_message)


@app.route("/records")
def show_records():
    session = Session()
    records = session.query(Record).all()
    session.close()
    return render_template("records.html", records=records)


if __name__ == "__main__":
    # Запуск на localhost:5000
    app.run(host="127.0.0.1", port=5000, debug=True)
