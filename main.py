from log_config import logger
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_ollama import ChatOllama
import os
import shutil
from datetime import datetime

LOG_FILE = "latest.log"
LOGS_DIR = "logs"
LOG_SAVE_STATE = ""
os.makedirs(LOGS_DIR, exist_ok=True)
if os.path.isfile(LOG_FILE):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    new_name = f"agent_{timestamp}.log"
    dest_path = os.path.join(LOGS_DIR, new_name)
    
    try:
        shutil.copy2(LOG_FILE, dest_path)
        LOG_SAVE_STATE = f"Лог сохранён по пути {dest_path}"
    except Exception as e:
        LOG_SAVE_STATE = f"Невозможно сохранить лог: {e}"

from agent import chunk_answer, whole_answer
from tools import (
    search_tool, 
    read_file, 
    write_file, 
    search_in_files, 
    list_files, 
    create_directory, # <-- НОВЫЙ ИНСТРУМЕНТ
    copy_files, 
    move_files, 
    delete_objects
)
import sqlite3, json
import platform
from log_config import logger

logger.info(LOG_SAVE_STATE)
logger.info("Сессия запущена")
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
logger.info(f"Конфиг (без ключа): {json.dumps({k: v for k, v in config.items() if k != 'api_key'}, ensure_ascii=False, indent=2)}")
model = config["model"]
api_key = config["api_key"]
provider = config["provider"]
if provider == "ollama":
    llm = ChatOllama(
        model=model, 
        temperature=config["temperature"]
    )
elif provider in ["openrouter", "openai"]:
    from langchain_openai import ChatOpenAI
    base_url = "https://openrouter.ai/api/v1" if provider == "openrouter" else None
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=config["temperature"]
    )
elif provider == "anthropic":
    from langchain_anthropic import ChatAnthropic
    llm = ChatAnthropic(
        model=model,
        api_key=api_key,
        temperature=config["temperature"]
    )
else:
    raise ValueError(f"Неизвестный провайдер: {provider}")

logger.info(f"Выбранная модель: {model}")
logger.info(f"Провайдер: {provider}")
conn = sqlite3.connect(config["memory_file"], check_same_thread=False)
memory = SqliteSaver(conn)
tools=[search_tool, read_file, write_file, search_in_files, list_files, create_directory, copy_files, move_files, delete_objects]
all_tools = []
for tl in tools:
    all_tools.append(f"{tl.name}")
logger.info(f"Инструменты ({len(all_tools)}): {", ".join(all_tools)}")
agent = create_agent(
    model=llm, 
    tools=tools,
    checkpointer=memory 
)
logger.info("Агент готов к работе. Введите 'выход' для завершения.")
system_info = f"\n[SYSTEM INFO] Запущен новый сеанс агента\nТекущая ОС: {platform.system()}\nДиректория агента: {os.getcwd()}\nПредпочитаемая рабочая директория: {config["preferred_dir"]}"

if config.get("o_format") == "chunk":
    while True:
        try:    
            prompt = input("Вы: ").strip()
            if prompt.lower() in ["exit", "quit", "выход"]:
                logger.info("Диалог завершен")
                print("\nДо свидания!")
                break
            else:
                logger.info(f"Запрос пользователя: {prompt}")
                ans=chunk_answer(prompt=prompt+system_info,agent=agent,agent_config=config["agent_config"])
                system_info = ''
                if ans=="fatal":
                    print("Фатальная ошибка! Смотрите лог")
                    break
        except KeyboardInterrupt:
            logger.info("Диалог завершен: Принудительный выход")
            print("\nПринудительный выход")
            break
else:
    while True:
        try:    
            prompt = input("Вы: ").strip()
            if prompt.lower() in ["exit", "quit", "выход"]:
                logger.info("Диалог завершен")
                print("\nДо свидания!")
                break
            else:
                logger.info(f"Запрос пользователя: {prompt}")
                ans=whole_answer(prompt=prompt,agent=agent,agent_config=config["agent_config"])
                if ans!="fatal":
                    print(ans)
                    system_info = ''
                else:
                    print("Фатальная ошибка! Смотрите лог")
                    break
        except KeyboardInterrupt:
            logger.info("Диалог завершен: Принудительный выход")
            print("\nПринудительный выход")