# 🚀 Быстрый запуск BPMN Конвертера

## Автоматический запуск (рекомендуется)

```bash
python3 start_service.py
```

Скрипт автоматически:
- Проверит версию Python
- Создаст виртуальное окружение
- Установит зависимости
- Запустит бэкенд (порт 5001)
- Запустит фронтенд (порт 8080)
- Откроет браузер

## Ручной запуск

### 1. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# или
venv\Scripts\activate     # Windows
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Запуск бэкенда

```bash
cd backend
python app.py
```

Бэкенд будет доступен по адресу: `http://localhost:5001`

### 4. Запуск фронтенда

```bash
# В новом терминале
cd frontend
python3 -m http.server 8080
```

Фронтенд будет доступен по адресу: `http://localhost:8080`

## Тестирование API

### Проверка работы сервиса

```bash
curl -s http://localhost:5001/api/health
```

### Валидация BPMN файла

```bash
curl -X POST -F "file=@examples/example_bpmn18.xml" http://localhost:5001/api/validate
```

### Конвертация BPMN файла

```bash
curl -X POST -F "file=@examples/example_bpmn19_complex.xml" http://localhost:5001/api/convert -o converted.xml
```

## Устранение неисправностей

### Порт 5001 занят

```bash
# Найти процесс
lsof -i :5001

# Убить процесс
kill -9 <PID>
```

### Проблемы с установкой lxml

На macOS может потребоваться:

```bash
# Установить инструменты разработки
xcode-select --install

# Или использовать Homebrew
brew install libxml2 libxslt
```

### Проблемы с Python 3.13

Если возникают проблемы с externally-managed-environment:

```bash
# Используйте виртуальное окружение (рекомендуется)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Структура проекта

```
bpmn_upgrade/
├── backend/           # Flask API
├── frontend/          # HTML интерфейс
├── examples/          # Примеры BPMN файлов
├── venv/             # Виртуальное окружение
├── requirements.txt   # Зависимости Python
└── start_service.py  # Автоматический запуск
```

## Поддержка

Если возникли проблемы:
1. Проверьте версию Python (требуется 3.8+)
2. Убедитесь, что виртуальное окружение активировано
3. Проверьте логи в терминале
4. Убедитесь, что порты 5001 и 8080 свободны

Подробная документация: [README.md](README.md) 