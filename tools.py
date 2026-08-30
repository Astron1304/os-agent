from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from pathlib import Path
import os, shutil
from log_config import *

search_tool = DuckDuckGoSearchRun()

@tool
def read_file(file_path: str) -> str:
    """Читает содержимое файла. Путь должен быть абсолютным или относительным."""
    logger.info(f"Инструмент read_file начал работу с файлом {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            logger.info(f"Инструмент read_file завершил работу. Файл {file_path} успешно прочитан")
            return f.read()
    except Exception as e:
        logger.error(f"Ошибка чтения файла {file_path}: {str(e)}")
        return f"Ошибка чтения файла {file_path}: {str(e)}"

@tool
def write_file(file_path: str, content: str) -> str:
    """Записывает текст в файл. Если файл существует - перезаписывает."""
    logger.info(f"Инструмент write_file начал работу с файлом {file_path}")

    try:
        # Создаем папки, если их нет
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
        logger.debug(f"Инструмент write_file завершил работу. Файл {file_path} успешно сохранён")
        return f"Файл успешно сохранен: {file_path}"
    except Exception as e:
        logger.error(f"Ошибка записи файла {file_path}: {str(e)}")
        return f"Ошибка записи файла {file_path}: {str(e)}"


@tool
def list_files(directory_path: str) -> str:
    """Показывает список файлов и папок в указанной директории."""
    logger.info(f"Инструмент list_files начал работу в папке {directory_path}")
    try:
        items = os.listdir(directory_path)
        files = [f for f in items if os.path.isfile(os.path.join(directory_path, f))]
        dirs = [d for d in items if os.path.isdir(os.path.join(directory_path, d))]
        
        result = f"Папки: {', '.join(dirs) if dirs else 'нет'}\n"
        result += f"Файлы: {', '.join(files) if files else 'нет'}"

        logger.debug(f"Инструмент list_files завершил работу. Найдено: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка чтения папки {directory_path}: {str(e)}")
        return f"Ошибка чтения папки {directory_path}: {str(e)}"

@tool
def search_in_files(directory_path: str, search_text: str) -> str:
    """Ищет текст во всех файлах в папке (рекурсивно)."""
    logger.info(f"Инструмент search_in_files начал работу в папке {directory_path}")

    results = []

    try:
        for root, files in os.walk(directory_path):
            for file in files:
                if file.endswith(('.txt', '.py', '.md', '.json')):  # только текстовые файлы
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if search_text.lower() in content.lower():
                                results.append(f"Найдено в: {file_path}")
                    except:
                        pass

        if results:
            all_results = "\n".join(results)
            logger.debug(f"Инструмент search_in_files завершил работу. Текст \"{search_text}\" найден в следующих файлах: {all_results}") 
            return "\n".join(results) 
        else:
            logger.debug(f"Инструмент search_in_files завершил работу. Текст \"{search_text}\" не найден")
            return  "Ничего не найдено"
    except Exception as e:
        logger.error(f"Ошибка поиска: {str(e)}")
        return f"Ошибка поиска: {str(e)}"

@tool
def create_directory(dir_path: str) -> str:
    """Создает новую пустую папку по указанному пути. Создает все промежуточные папки, если их нет."""
    logger.info(f"Инструмент create_directory начал работу. Путь: {dir_path}")
    try:
        # resolve() делает путь абсолютным и нормализует его (убирает лишние слеши и точки)
        target_path = Path(dir_path).resolve()
        target_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Папка успешно создана: {target_path}")
        return f"Папка успешно создана: {target_path}"
    except Exception as e:
        logger.error(f"Ошибка создания папки {dir_path}: {str(e)}")
        return f"Ошибка создания папки: {str(e)}"

@tool
def copy_files(src_path: str, dst_path: str, files: list) -> str:
    """Копирует список файлов из одной директории в другую."""
    logger.info(f"Инструмент copy_files начал работу. Источник: {src_path}, Назначение: {dst_path}")
    
    errs = 0
    list_errs = {}
    
    try:
        # resolve() превращает пути в абсолютные и безопасные
        src = Path(src_path).resolve()
        # Если dst относительный, считаем его относительно src, иначе как абсолютный
        dst = (src / dst_path).resolve() if not Path(dst_path).is_absolute() else Path(dst_path).resolve()
        
        # Гарантированно создаем папку назначения
        dst.mkdir(parents=True, exist_ok=True)
        
        for f in files:
            shutil.copy(src=src / f, dst=dst / f)
    except Exception as e:
        errs += 1
        list_errs[f] = str(e)

    if errs == 0:
        logger.debug(f"Инструмент copy_files завершил работу. {len(files)} файлов было скопировано из папки {src_path} в папку {dst_path}.")
        return f"Файлы были скопированы из папки {src_path} в папку {dst_path}. Ошибок не обнаружено"
    else:
        err_details = ""
        for obj in list_errs:
            err_details += f"\n\t{str(Path(src_path)/obj)}: {list_errs[obj]}" 
        logger.error(f"Инструмент copy_files завершил работу. Ошибок при копировании {len(files)} файлов: {errs}. Полный лог: {err_details}")
        return f"Файлы были скопированы из папки {src_path} в папку {dst_path}. Обнаружено ошибок: {errs}"


@tool
def move_files(src_path: str, dst_path: str, files: list) -> str:
    """Перемещает список файлов из одной директории в другую."""
    logger.info(f"Инструмент move_files начал работу. Источник: {src_path}, Назначение: {dst_path}")
    
    src = Path(src_path).resolve()
    if src == Path.cwd().resolve():
        logger.error("Попытка перемещения из рабочей директории заблокирована")
        return "Невозможно переместить файлы из текущей рабочей директории агента"
        
    errs = 0
    list_errs = {}
    
    try:
        dst = (src / dst_path).resolve() if not Path(dst_path).is_absolute() else Path(dst_path).resolve()
        dst.mkdir(parents=True, exist_ok=True)
        
        for f in files:
            shutil.move(src=str(src / f), dst=str(dst / f))
            
    except Exception as e:
        errs += 1
        list_errs[f] = str(e)

    if errs == 0:
        logger.debug(f"Инструмент move_files завершил работу. {len(files)} файлов было перемещено из папки {src_path} в папку {dst_path}.")
        return f"Файлы были перемещены из папки {src_path} в папку {dst_path}. Ошибок не обнаружено"
    else:
        err_details = ""
        for obj in list_errs:
            err_details += f"\n\t{str(Path(src_path)/obj)}: {list_errs[obj]}" 
        logger.error(f"Инструмент move_files завершил работу. Ошибок при перемещении {len(files)} файлов: {errs}. Полный лог: {err_details}")
        return f"Файлы были перемещены из папки {src_path} в папку {dst_path}. Обнаружено ошибок: {errs}"
@tool
def move_files(src_path: str, dst_path: str, files: list) -> str:
    """Перемещает список файлов из одной директории в другую. Создаёт директорию назначения, если ее не было до этого."""
    logger.info(f"Инструмент move_files начал работу. Источник: {src_path}. Место назначения: {dst_path}")

    if Path(src_path).resolve() == Path(os.getcwd()).resolve():
        logger.error(f"Инструмент move_files завершил работу с ошибкой: невозможно переместить файлы из рабочей директории {src_path}")
        return "Невозможно переместить файлы из рабочей директории"

    errs = 0
    list_errs = {}

    # 1. ГАРАНТИРОВАННО создаем папку назначения ПЕРЕД перемещением
    Path(dst_path).mkdir(parents=True, exist_ok=True)

    for f in files:
        try:
            # 2. ИСПРАВЛЕНО: dst должен включать имя файла (Path(dst_path) / f)
            shutil.move(src=str(Path(src_path) / f), dst=str(Path(dst_path) / f))
        except Exception as e:
            errs += 1
            list_errs[f] = str(e)

    if errs == 0:
        logger.debug(f"Инструмент move_files завершил работу. {len(files)} файлов было перемещено из папки {src_path} в папку {dst_path}.")
        return f"Файлы были перемещены из папки {src_path} в папку {dst_path}. Ошибок не обнаружено"
    else:
        err_details = ""
        for obj in list_errs:
            err_details += f"\n\t{str(Path(src_path)/obj)}: {list_errs[obj]}" 
        logger.error(f"Инструмент move_files завершил работу. Ошибок при перемещении {len(files)} файлов: {errs}. Полный лог: {err_details}")
        return f"Файлы были перемещены из папки {src_path} в папку {dst_path}. Обнаружено ошибок: {errs}"

@tool
def delete_objects(directory_path: str, objects: list)->str:
    """Удаляет список файлов и папок из целевой директории"""
    logger.info(f"Инструмент delete_objects начал работу в папке {directory_path}")

    if Path(directory_path).resolve() == Path(os.getcwd()).resolve():
        logger.error(f"Инструмент delete_objects завершил работу с ошибкой: невозможно удалить объекты из рабочей директории {directory_path}")
        return "Невозможно удалить объекты из рабочей директории"

    errs = 0
    list_errs = {}

    for f in objects:
        obj_path = Path(directory_path)/f
        try:
            if obj_path.is_file():
                os.remove(obj_path)
            elif obj_path.is_dir():
                shutil.rmtree(obj_path)
        except Exception as e:
                errs+=1
                list_errs[f] = str(e)

    if errs == 0:
        logger.debug(f"Инструмент delete_objects завершил работу. {len(objects)} объектов было удалено из папки {directory_path}.")
        return f"Объекты были удалены из папки {directory_path}. Ошибок не обнаружено"
    else:
        err_details = ""
        for obj in list_errs:
            err_details += f"\n\t{str(Path(directory_path)/obj)}: {list_errs[obj]}" 
        logger.error(f"Инструмент delete_objects завершил работу. Ошибок при удалении {len(objects)} объектов: {errs}. Полный лог: {err_details}")
        return f"Объекты были удалены из папки {directory_path}. Обнаружено ошибок: {errs}"