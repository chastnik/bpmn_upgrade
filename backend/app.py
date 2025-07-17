from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from werkzeug.utils import secure_filename
from bpmn_converter import BPMNConverter
import traceback

app = Flask(__name__)
CORS(app)

# Конфигурация
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

# Создаём папки если их нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'xml', 'bpmn'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервиса"""
    return jsonify({'status': 'OK', 'message': 'BPMN Converter Service is running'})

@app.route('/api/convert', methods=['POST'])
def convert_bpmn():
    """Конвертация BPMN файла"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_path)
            
            # Конвертация
            converter = BPMNConverter()
            
            # Определяем выходное имя файла
            output_filename = f"converted_{filename}"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            
            # Выполняем конвертацию
            success = converter.convert_to_bpmn20(input_path, output_path)
            
            if success:
                # Возвращаем результат
                return send_file(output_path, 
                               as_attachment=True, 
                               download_name=output_filename,
                               mimetype='application/xml')
            else:
                return jsonify({'error': 'Ошибка конвертации BPMN'}), 500
        else:
            return jsonify({'error': 'Недопустимый формат файла. Разрешены только .xml и .bpmn'}), 400
            
    except Exception as e:
        app.logger.error(f'Ошибка при конвертации: {str(e)}')
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'Внутренняя ошибка сервера: {str(e)}'}), 500

@app.route('/api/validate', methods=['POST'])
def validate_bpmn():
    """Валидация BPMN файла"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            temp_path = os.path.join(tempfile.gettempdir(), filename)
            file.save(temp_path)
            
            # Валидация
            converter = BPMNConverter()
            validation_result = converter.validate_bpmn(temp_path)
            
            # Удаляем временный файл
            os.remove(temp_path)
            
            return jsonify(validation_result)
        else:
            return jsonify({'error': 'Недопустимый формат файла. Разрешены только .xml и .bpmn'}), 400
            
    except Exception as e:
        app.logger.error(f'Ошибка при валидации: {str(e)}')
        return jsonify({'error': f'Внутренняя ошибка сервера: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 