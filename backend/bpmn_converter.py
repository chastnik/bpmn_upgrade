import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

class BPMNConverter:
    """Конвертер BPMN файлов из версии 1.8/1.9 в версию 2.0"""
    
    def __init__(self):
        self.namespaces = {
            'bpmn18': 'http://www.omg.org/BPMN20/2010/04/1.0',
            'bpmn19': 'http://www.omg.org/BPMN20/2009/10/1.0',
            'bpmn20': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
            'omgdc': 'http://www.omg.org/spec/DD/20100524/DC',
            'omgdi': 'http://www.omg.org/spec/DD/20100524/DI',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'tns': 'http://www.activiti.org/bpmn'
        }
        
        # Маппинг элементов BPMN 1.8/1.9 -> 2.0
        self.element_mapping = {
            'startEvent': 'startEvent',
            'endEvent': 'endEvent',
            'task': 'task',
            'userTask': 'userTask',
            'serviceTask': 'serviceTask',
            'scriptTask': 'scriptTask',
            'businessRuleTask': 'businessRuleTask',
            'receiveTask': 'receiveTask',
            'sendTask': 'sendTask',
            'manualTask': 'manualTask',
            'exclusiveGateway': 'exclusiveGateway',
            'parallelGateway': 'parallelGateway',
            'inclusiveGateway': 'inclusiveGateway',
            'complexGateway': 'complexGateway',
            'sequenceFlow': 'sequenceFlow',
            'messageFlow': 'messageFlow',
            'association': 'association',
            'dataObject': 'dataObject',
            'dataStore': 'dataStore',
            'subprocess': 'subProcess',
            'callActivity': 'callActivity',
            'intermediateCatchEvent': 'intermediateCatchEvent',
            'intermediateThrowEvent': 'intermediateThrowEvent',
            'boundaryEvent': 'boundaryEvent'
        }
    
    def validate_bpmn(self, file_path: str) -> Dict[str, Any]:
        """Валидация BPMN файла"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Определяем версию BPMN
            namespace = root.tag.split('}')[0].strip('{') if '}' in root.tag else ''
            version = self._detect_bpmn_version(namespace, root)
            
            # Проверяем структуру - ищем процессы в разных форматах
            processes = []
            
            # Стандартные BPMN процессы
            processes.extend(root.findall('.//process'))
            processes.extend(root.findall('.//{*}process'))
            
            # Нестандартные форматы
            processes.extend(root.findall('.//Process'))
            processes.extend(root.findall('.//BusinessProcessDiagram'))
            processes.extend(root.findall('.//{*}Process'))
            processes.extend(root.findall('.//{*}BusinessProcessDiagram'))
            
            # Считаем все элементы
            total_elements = len(root.findall('.//*'))
            
            return {
                'valid': True,
                'version': version,
                'processes': len(processes),
                'elements': total_elements,
                'message': f'Файл валиден. Обнаружена версия BPMN {version}',
                'format': 'Custom' if 'Custom' in version else 'Standard'
            }
        except ET.ParseError as e:
            return {
                'valid': False,
                'error': f'Ошибка парсинга XML: {str(e)}',
                'message': 'Файл не является валидным XML'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Ошибка валидации: {str(e)}',
                'message': 'Не удалось валидировать файл'
            }
    
    def _detect_bpmn_version(self, namespace: str, root: ET.Element) -> str:
        """Определение версии BPMN по namespace и структуре"""
        # Стандартные namespace версии
        if 'bpmn20' in namespace or '2010/04' in namespace or '20100524' in namespace:
            return '2.0'
        elif 'bpmn19' in namespace or '2009/10' in namespace:
            return '1.9'
        elif 'bpmn18' in namespace or '2008/06' in namespace:
            return '1.8'
        
        # Проверяем нестандартные форматы
        # Для файлов с корневым элементом <BPMN BPMNVersion="X.X">
        if root.tag == 'BPMN' and root.get('BPMNVersion'):
            return root.get('BPMNVersion')
        
        # Для файлов с корневым элементом <bpmn:definitions>
        if root.tag.endswith('definitions'):
            if root.get('targetNamespace'):
                return '1.8/1.9'
        
        # Проверяем атрибуты версии в корневом элементе
        version_attrs = ['version', 'Version', 'BPMNVersion', 'bpmnVersion']
        for attr in version_attrs:
            if root.get(attr):
                return root.get(attr)
        
        # Пробуем определить по дочерним элементам
        for child in root:
            if 'BusinessProcessDiagram' in child.tag:
                return '1.9 (Custom)'
            elif 'process' in child.tag.lower():
                return '1.8/1.9'
        
        return 'unknown'
    
    def convert_to_bpmn20(self, input_path: str, output_path: str) -> bool:
        """Конвертация BPMN файла в версию 2.0"""
        try:
            # Парсим входной файл
            tree = ET.parse(input_path)
            root = tree.getroot()
            
            # Определяем версию
            namespace = root.tag.split('}')[0].strip('{') if '}' in root.tag else ''
            version = self._detect_bpmn_version(namespace, root)
            
            if version == '2.0':
                # Файл уже в формате 2.0, просто копируем
                tree.write(output_path, encoding='utf-8', xml_declaration=True)
                return True
            
            # Создаем новый BPMN 2.0 документ
            bpmn20_root = self._create_bpmn20_structure()
            
            # Проверяем тип файла и конвертируем соответственно
            if 'Custom' in version or root.tag == 'BPMN':
                # Нестандартный формат - специальная обработка
                self._convert_custom_format(root, bpmn20_root)
            else:
                # Стандартный формат
                self._convert_processes(root, bpmn20_root)
                self._convert_diagrams(root, bpmn20_root)
            
            # Сохраняем результат
            self._save_formatted_xml(bpmn20_root, output_path)
            
            return True
            
        except Exception as e:
            print(f"Ошибка конвертации: {str(e)}")
            return False
    
    def _create_bpmn20_structure(self) -> ET.Element:
        """Создание базовой структуры BPMN 2.0"""
        root = ET.Element('definitions')
        root.set('xmlns', self.namespaces['bpmn20'])
        root.set('xmlns:bpmndi', self.namespaces['bpmndi'])
        root.set('xmlns:omgdc', self.namespaces['omgdc'])
        root.set('xmlns:omgdi', self.namespaces['omgdi'])
        root.set('xmlns:xsi', self.namespaces['xsi'])
        root.set('targetNamespace', 'http://www.activiti.org/bpmn')
        root.set('exporter', 'BPMN Converter')
        root.set('exporterVersion', '1.0')
        
        return root
    
    def _convert_processes(self, old_root: ET.Element, new_root: ET.Element):
        """Конвертация процессов"""
        # Находим все процессы в старом формате
        processes = old_root.findall('.//process') or old_root.findall('.//{*}process')
        
        for old_process in processes:
            new_process = ET.SubElement(new_root, 'process')
            
            # Копируем атрибуты процесса
            process_id = old_process.get('id', f'process_{len(new_root.findall("process")) + 1}')
            new_process.set('id', process_id)
            new_process.set('isExecutable', old_process.get('isExecutable', 'true'))
            
            if old_process.get('name'):
                new_process.set('name', old_process.get('name'))
            
            # Конвертируем элементы процесса
            self._convert_process_elements(old_process, new_process)
    
    def _convert_process_elements(self, old_process: ET.Element, new_process: ET.Element):
        """Конвертация элементов процесса"""
        for child in old_process:
            element_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            if element_name in self.element_mapping:
                self._convert_element(child, new_process, self.element_mapping[element_name])
    
    def _convert_element(self, old_element: ET.Element, parent: ET.Element, new_tag: str):
        """Конвертация отдельного элемента"""
        new_element = ET.SubElement(parent, new_tag)
        
        # Копируем основные атрибуты
        for attr_name, attr_value in old_element.attrib.items():
            if attr_name not in ['xmlns', 'xmlns:xsi']:
                new_element.set(attr_name, attr_value)
        
        # Обрабатываем специфичные элементы
        if new_tag == 'sequenceFlow':
            self._convert_sequence_flow(old_element, new_element)
        elif new_tag in ['startEvent', 'endEvent', 'intermediateCatchEvent', 'intermediateThrowEvent']:
            self._convert_event(old_element, new_element)
        elif new_tag in ['exclusiveGateway', 'parallelGateway', 'inclusiveGateway']:
            self._convert_gateway(old_element, new_element)
        elif 'Task' in new_tag:
            self._convert_task(old_element, new_element)
        
        # Копируем дочерние элементы
        for child in old_element:
            child_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child_name in ['documentation', 'extensionElements']:
                new_child = ET.SubElement(new_element, child_name)
                new_child.text = child.text
                for attr_name, attr_value in child.attrib.items():
                    new_child.set(attr_name, attr_value)
    
    def _convert_sequence_flow(self, old_element: ET.Element, new_element: ET.Element):
        """Конвертация sequence flow"""
        # Обработка условных выражений
        condition = old_element.find('.//conditionExpression') or old_element.find('.//{*}conditionExpression')
        if condition is not None:
            new_condition = ET.SubElement(new_element, 'conditionExpression')
            new_condition.set('xsi:type', 'tFormalExpression')
            new_condition.text = condition.text
    
    def _convert_event(self, old_element: ET.Element, new_element: ET.Element):
        """Конвертация событий"""
        # Обработка определений событий
        for event_def in old_element:
            event_def_name = event_def.tag.split('}')[-1] if '}' in event_def.tag else event_def.tag
            if event_def_name.endswith('EventDefinition'):
                new_event_def = ET.SubElement(new_element, event_def_name)
                for attr_name, attr_value in event_def.attrib.items():
                    new_event_def.set(attr_name, attr_value)
    
    def _convert_gateway(self, old_element: ET.Element, new_element: ET.Element):
        """Конвертация шлюзов"""
        # Шлюзы обычно не требуют специальной обработки
        pass
    
    def _convert_task(self, old_element: ET.Element, new_element: ET.Element):
        """Конвертация задач"""
        # Обработка специфичных атрибутов задач
        pass
    
    def _convert_diagrams(self, old_root: ET.Element, new_root: ET.Element):
        """Конвертация диаграмм"""
        # Поиск диаграмм в старом формате
        diagrams = old_root.findall('.//BPMNDiagram') or old_root.findall('.//{*}BPMNDiagram')
        
        for old_diagram in diagrams:
            new_diagram = ET.SubElement(new_root, 'bpmndi:BPMNDiagram')
            
            if old_diagram.get('id'):
                new_diagram.set('id', old_diagram.get('id'))
            
            # Конвертируем плоскость диаграммы
            planes = old_diagram.findall('.//BPMNPlane') or old_diagram.findall('.//{*}BPMNPlane')
            for old_plane in planes:
                new_plane = ET.SubElement(new_diagram, 'bpmndi:BPMNPlane')
                
                if old_plane.get('id'):
                    new_plane.set('id', old_plane.get('id'))
                if old_plane.get('bpmnElement'):
                    new_plane.set('bpmnElement', old_plane.get('bpmnElement'))
    
    def _convert_custom_format(self, old_root: ET.Element, new_root: ET.Element):
        """Конвертация нестандартного формата BPMN"""
        # Ищем BusinessProcessDiagram элементы
        diagrams = old_root.findall('.//BusinessProcessDiagram')
        
        for diagram in diagrams:
            # Создаем новый процесс
            new_process = ET.SubElement(new_root, 'process')
            
            # Получаем ID и имя из диаграммы
            process_id = diagram.get('id', 'process_1').strip('()')
            process_name = ''
            
            # Ищем имя процесса
            name_elem = diagram.find('Name')
            if name_elem is not None and name_elem.text:
                process_name = name_elem.text
            
            new_process.set('id', process_id)
            new_process.set('isExecutable', 'true')
            if process_name:
                new_process.set('name', process_name)
            
            # Ищем Process элементы внутри диаграммы
            processes = diagram.findall('.//Process')
            
            for process in processes:
                # Конвертируем элементы процесса
                self._convert_custom_process_elements(process, new_process)
            
            # Если процессов нет, создаем минимальный процесс
            if not processes:
                # Создаем простое стартовое событие
                start_event = ET.SubElement(new_process, 'startEvent')
                start_event.set('id', 'start_1')
                start_event.set('name', 'Start')
                
                # Создаем конечное событие
                end_event = ET.SubElement(new_process, 'endEvent')
                end_event.set('id', 'end_1')
                end_event.set('name', 'End')
    
    def _convert_custom_process_elements(self, old_process: ET.Element, new_process: ET.Element):
        """Конвертация элементов из нестандартного формата"""
        # Обрабатываем различные типы элементов
        
        # Обрабатываем Tasks
        tasks = old_process.findall('.//Tasks')
        for task_group in tasks:
            for task in task_group:
                if task.tag != 'Tasks':
                    new_task = ET.SubElement(new_process, 'task')
                    task_id = task.get('id', '').strip('()')
                    if task_id:
                        new_task.set('id', task_id)
                    
                    # Ищем имя задачи
                    name_elem = task.find('Name')
                    if name_elem is not None and name_elem.text:
                        new_task.set('name', name_elem.text)
        
        # Обрабатываем SubProcesses
        subprocesses = old_process.findall('.//SubProcesses')
        for subprocess_group in subprocesses:
            for subprocess in subprocess_group:
                if subprocess.tag == 'SubProcess':
                    new_subprocess = ET.SubElement(new_process, 'subProcess')
                    subprocess_id = subprocess.get('id', '').strip('()')
                    if subprocess_id:
                        new_subprocess.set('id', subprocess_id)
                    
                    # Ищем имя подпроцесса
                    name_elem = subprocess.find('Name')
                    if name_elem is not None and name_elem.text:
                        new_subprocess.set('name', name_elem.text)
        
        # Обрабатываем Events
        events = old_process.findall('.//Events')
        for event_group in events:
            for event in event_group:
                if event.tag != 'Events':
                    # Определяем тип события по имени тега
                    event_type = 'intermediateThrowEvent'
                    if 'Start' in event.tag:
                        event_type = 'startEvent'
                    elif 'End' in event.tag:
                        event_type = 'endEvent'
                    
                    new_event = ET.SubElement(new_process, event_type)
                    event_id = event.get('id', '').strip('()')
                    if event_id:
                        new_event.set('id', event_id)
                    
                    # Ищем имя события
                    name_elem = event.find('Name')
                    if name_elem is not None and name_elem.text:
                        new_event.set('name', name_elem.text)
        
        # Обрабатываем Gateways
        gateways = old_process.findall('.//Gateways')
        for gateway_group in gateways:
            for gateway in gateway_group:
                if gateway.tag != 'Gateways':
                    new_gateway = ET.SubElement(new_process, 'exclusiveGateway')
                    gateway_id = gateway.get('id', '').strip('()')
                    if gateway_id:
                        new_gateway.set('id', gateway_id)
                    
                    # Ищем имя шлюза
                    name_elem = gateway.find('Name')
                    if name_elem is not None and name_elem.text:
                        new_gateway.set('name', name_elem.text)

    def _save_formatted_xml(self, root: ET.Element, output_path: str):
        """Сохранение XML с форматированием"""
        # Преобразуем в строку
        xml_str = ET.tostring(root, encoding='unicode')
        
        # Форматируем
        dom = minidom.parseString(xml_str)
        formatted_xml = dom.toprettyxml(indent='  ', encoding='utf-8')
        
        # Сохраняем в файл
        with open(output_path, 'wb') as f:
            f.write(formatted_xml) 