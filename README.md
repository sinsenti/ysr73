# Инструкция по развертыванию

***

> **ВАЖНО:** во всех командах и конфигурационных файлах этого руководства под `project` имеется в виду папка с вашим проектом. Заменяйте `project` на реальный путь к папке вашего проекта, который вы используете у себя, например `/home/ubuntu/project` в моем случае или другой.


## Шаг 1. Подготовка сервера Ubuntu

1. Обновите пакеты и установите необходимые зависимости:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv postgresql postgresql-contrib nginx git daemon -y
```

***

## Шаг 2. Настройка PostgreSQL

1. Переключитесь на пользователя postgres и войдите в консоль psql:

```bash
sudo -i -u postgres
psql
```

2. Создайте базу данных, пользователя для проекта и передайте ему прав на изменения таблицы(делаем так же владельцем, чтобы были у пользователя были точно были все права):

```sql
CREATE DATABASE testdb;
CREATE USER testuser WITH PASSWORD 'testpassword'; GRANT ALL PRIVILEGES ON DATABASE testdb TO testuser; ```

3. Выйти из postgresql:

```sql
\q
exit
```

***

## Шаг 3. Клонирование и подготовка проекта

1. Скопируйте репозиторий вашего проекта или создайте директорию:

```bash
git clone https://github.com/sinsenti/TODO.git
mkdir -p ~/project
cd ~/project
```

2. Создайте виртуальное окружение и активируйте его:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Установите зависимости:

```bash
pip install -r requirements.txt
```

***

## Шаг 4. Настройка systemd-сервиса для gunicorn

1. Создайте файл сервиса systemd для gunicorn:

```bash
sudo vi /etc/systemd/system/gunicorn.service
```

2. Вставьте следующий конфиг (замените пути и имя пользователя на свои):
- Вместо ubuntu(User) введите ваше имя аккаунта.
- И указывайте ваш путь к проекту(в 4 местах в этом конфиге)


```config
[Unit]
Description=gunicorn daemon for Flask app
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/project
Environment="PATH=/home/ubuntu/project/venv/bin"
ExecStart=/home/ubuntu/project/venv/bin/gunicorn --workers 3 --bind unix:/home/ubuntu/project/gunicorn.sock app:app

[Install]
WantedBy=multi-user.target
```

3. Дайте разрешение для сокет файла:

```bash
sudo chown ubuntu:www-data /home/ubuntu/project/gunicorn.sock
sudo chmod 660 /home/ubuntu/project/gunicorn.sock
```

4. Запустите и включите сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

5. Проверьте статус сервиса:

```bash
sudo systemctl status gunicorn
```

***

## Шаг 5. Настройка nginx для проксирования запросов

1. Создайте файл конфигурации nginx:

```bash
sudo vi /etc/nginx/sites-available/project.conf
```

2. Вставьте следующий конфиг:

```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://unix:/home/ubuntu/project/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Активируйте конфигурацию и проверьте корректность конфига:

```bash
sudo ln -s /etc/nginx/sites-available/project.conf /etc/nginx/sites-enabled/
sudo nginx -t
```

4. Перезапустите nginx:

```bash
sudo systemctl reload nginx
```

***

## Шаг 6. Проверка работы приложения

- Откройте браузер и перейдите по адресу: http://localhost.
- Должна открыться страница загрузки JSON файла.
- Тестируйте приложение

***

## Дополнительно:

- Для отладки можно запускать Flask напрямую командой:

```bash
python app.py
```

- Для изменения проекта, при изменении кода приложения или шаблонов не забудьте перезапустить gunicorn:

```bash
sudo systemctl restart gunicorn
```

***

# Пример файла requirements.txt

```
blinker==1.9.0
click==8.2.1
Flask==3.1.1
greenlet==3.2.4
gunicorn==23.0.0
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.2
packaging==25.0
psycopg2-binary==2.9.10
SQLAlchemy==2.0.43
typing_extensions==4.14.1
Werkzeug==3.1.3
```

***
