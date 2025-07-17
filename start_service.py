#!/usr/bin/env python3
"""
Скрипт для запуска веб-сервиса конвертера BPMN
"""
import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} обнаружен")

def setup_virtual_environment():
    """Настройка виртуального окружения"""
    venv_path = Path(__file__).parent / 'venv'
    
    if not venv_path.exists():
        print("🔧 Создание виртуального окружения...")
        try:
            subprocess.run([sys.executable, '-m', 'venv', 'venv'], 
                          check=True, capture_output=True, text=True)
            print("✅ Виртуальное окружение создано")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка создания виртуального окружения: {e}")
            sys.exit(1)
    
    # Определяем путь к Python в виртуальном окружении
    if sys.platform == "win32":
        python_venv = venv_path / "Scripts" / "python.exe"
        pip_venv = venv_path / "Scripts" / "pip.exe"
    else:
        python_venv = venv_path / "bin" / "python"
        pip_venv = venv_path / "bin" / "pip"
    
    return str(python_venv), str(pip_venv)

def install_dependencies():
    """Установка зависимостей в виртуальное окружение"""
    print("📦 Установка зависимостей...")
    python_venv, pip_venv = setup_virtual_environment()
    
    try:
        subprocess.run([pip_venv, 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True, text=True)
        print("✅ Зависимости установлены")
        return python_venv
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        sys.exit(1)

def start_backend(python_venv):
    """Запуск бэкенда"""
    print("🚀 Запуск бэкенда...")
    
    # Переходим в директорию backend
    backend_dir = Path(__file__).parent / 'backend'
    os.chdir(backend_dir)
    
    # Запускаем Flask приложение с виртуальным окружением
    try:
        return subprocess.Popen([python_venv, 'app.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
    except Exception as e:
        print(f"❌ Ошибка запуска бэкенда: {e}")
        sys.exit(1)

def start_frontend():
    """Запуск фронтенда"""
    print("🌐 Запуск фронтенда...")
    
    # Переходим в директорию frontend
    frontend_dir = Path(__file__).parent / 'frontend'
    os.chdir(frontend_dir)
    
    # Запускаем HTTP сервер
    try:
        return subprocess.Popen([sys.executable, '-m', 'http.server', '8080'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
    except Exception as e:
        print(f"❌ Ошибка запуска фронтенда: {e}")
        sys.exit(1)

def wait_for_service(url, timeout=30):
    """Ожидание готовности сервиса"""
    import requests
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def main():
    """Основная функция"""
    print("🔄 Запуск конвертера BPMN версий")
    print("=" * 40)
    
    # Проверка Python версии
    check_python_version()
    
    # Установка зависимостей и получение пути к Python
    python_venv = install_dependencies()
    
    # Возвращаемся в корневую директорию
    os.chdir(Path(__file__).parent)
    
    # Запуск бэкенда
    backend_process = start_backend(python_venv)
    print("✅ Бэкенд запущен на порту 5000")
    
    # Ожидание готовности бэкенда
    print("⏳ Ожидание готовности бэкенда...")
    if wait_for_service("http://localhost:5001/api/health"):
        print("✅ Бэкенд готов к работе")
    else:
        print("❌ Бэкенд не отвечает")
        backend_process.terminate()
        sys.exit(1)
    
    # Запуск фронтенда
    frontend_process = start_frontend()
    print("✅ Фронтенд запущен на порту 8080")
    
    # Ожидание готовности фронтенда
    print("⏳ Ожидание готовности фронтенда...")
    if wait_for_service("http://localhost:8080"):
        print("✅ Фронтенд готов к работе")
    else:
        print("❌ Фронтенд не отвечает")
        frontend_process.terminate()
        backend_process.terminate()
        sys.exit(1)
    
    # Открытие браузера
    print("\n🌐 Открытие браузера...")
    webbrowser.open("http://localhost:8080")
    
    print("\n" + "=" * 40)
    print("✅ Сервис запущен!")
    print("📍 Веб-интерфейс: http://localhost:8080")
    print("🔧 API: http://localhost:5001/api")
    print("📚 Документация: README.md")
    print("\n💡 Нажмите Ctrl+C для остановки сервиса")
    print("=" * 40)
    
    try:
        # Ожидание завершения
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Остановка сервиса...")
        backend_process.terminate()
        frontend_process.terminate()
        
        # Ожидание завершения процессов
        backend_process.wait()
        frontend_process.wait()
        
        print("✅ Сервис остановлен")

if __name__ == "__main__":
    main() 