import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QTextBrowser, QLineEdit, QPushButton,
                              QLabel, QSplitter)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
import markdown

# Импортируем вашего агента
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from tools import (search_tool, read_file, write_file, search_in_files, 
                   list_files, copy_files, move_files, delete_objects)
import sqlite3


class AgentWorker(QThread):
    """Поток для работы агента без блокировки GUI"""
    chunk_received = pyqtSignal(str)  # Сигнал для каждого токена
    finished_signal = pyqtSignal(str)  # Сигнал завершения
    error_signal = pyqtSignal(str)  # Сигнал ошибки
    
    def __init__(self, prompt, agent, agent_config):
        super().__init__()
        self.prompt = prompt
        self.agent = agent
        self.agent_config = agent_config
        
    def run(self):
        try:
            from langchain_core.messages import HumanMessage
            question = {"messages": [HumanMessage(content=self.prompt)]}
            full_response = ""
            
            for chunk, metadata in self.agent.stream(question, config=self.agent_config, stream_mode="messages"):
                node = metadata.get("langgraph_node")
                if node == "model":
                    if hasattr(chunk, 'content') and chunk.content:
                        self.chunk_received.emit(chunk.content)
                        full_response += chunk.content
            
            self.finished_signal.emit(full_response)
            
        except Exception as e:
            self.error_signal.emit(str(e))


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ИИ-Агент с файловой системой")
        self.setGeometry(100, 100, 900, 700)
        
        # Инициализация агента
        self.init_agent()
        
        # Создание UI
        self.init_ui()
        
        # История чата (для Markdown)
        self.chat_history = []
        
    def init_agent(self):
        """Загрузка конфигурации и инициализация агента"""
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        self.llm = ChatOllama(
            model=config["model"],
            temperature=config["temperature"]
        )
        
        conn = sqlite3.connect(config["memory_file"], check_same_thread=False)
        memory = SqliteSaver(conn)
        
        tools = [search_tool, read_file, write_file, search_in_files, 
                 list_files, copy_files, move_files, delete_objects]
        
        self.agent = create_agent(
            model=self.llm,
            tools=tools,
            checkpointer=memory
        )
        
        self.agent_config = config["agent_config"]
        
    def init_ui(self):
        """Создание интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Заголовок
        title = QLabel("🤖 ИИ-Агент")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Область чата с Markdown
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setFont(QFont("Consolas", 11))
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.chat_display)
        
        # Поле ввода и кнопка
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setFont(QFont("Arial", 12))
        self.input_field.setPlaceholderText("Введите запрос...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        input_layout.addWidget(self.input_field)
        
        self.send_button = QPushButton("Отправить")
        self.send_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Статус-бар
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Приветственное сообщение
        self.add_message("system", "Привет! Я ваш ИИ-агент с доступом к файловой системе. Чем могу помочь?")
        
    def add_message(self, role, content):
        """Добавление сообщения в чат с Markdown-рендерингом"""
        self.chat_history.append({"role": role, "content": content})
        
        # Формируем HTML
        html_content = ""
        for msg in self.chat_history:
            if msg["role"] == "user":
                html_content += f'<div style="background-color: #e3f2fd; padding: 10px; margin: 5px 0; border-radius: 8px;">'
                html_content += f'<b>👤 Вы:</b><br>{msg["content"]}'
                html_content += '</div>'
            elif msg["role"] == "assistant":
                # Конвертируем Markdown в HTML
                md_content = markdown.markdown(
                    msg["content"],
                    extensions=['fenced_code', 'tables', 'nl2br']
                )
                html_content += f'<div style="background-color: #f1f8e9; padding: 10px; margin: 5px 0; border-radius: 8px;">'
                html_content += f'<b>🤖 Агент:</b><br>{md_content}'
                html_content += '</div>'
            elif msg["role"] == "system":
                html_content += f'<div style="background-color: #fff3e0; padding: 10px; margin: 5px 0; border-radius: 8px; font-style: italic;">'
                html_content += f'<b>ℹ️ Система:</b> {msg["content"]}'
                html_content += '</div>'
        
        self.chat_display.setHtml(html_content)
        
        # Автоскролл вниз
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_display.setTextCursor(cursor)
        
    def send_message(self):
        """Отправка сообщения"""
        prompt = self.input_field.text().strip()
        if not prompt:
            return
            
        # Добавляем сообщение пользователя
        self.add_message("user", prompt)
        self.input_field.clear()
        
        # Блокируем ввод
        self.send_button.setEnabled(False)
        self.input_field.setEnabled(False)
        self.status_label.setText("⏳ Агент думает...")
        
        # Добавляем пустое сообщение агента для стриминга
        self.chat_history.append({"role": "assistant", "content": ""})
        self.current_response_index = len(self.chat_history) - 1
        
        # Запускаем поток
        self.worker = AgentWorker(prompt, self.agent, self.agent_config)
        self.worker.chunk_received.connect(self.on_chunk_received)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()
        
    def on_chunk_received(self, chunk):
        """Обработка полученного токена"""
        self.chat_history[self.current_response_index]["content"] += chunk
        
        # Обновляем отображение
        self.update_display()
        
    def on_finished(self, full_response):
        """Завершение генерации"""
        self.send_button.setEnabled(True)
        self.input_field.setEnabled(True)
        self.status_label.setText("✅ Готово")
        self.input_field.setFocus()
        
    def on_error(self, error):
        """Обработка ошибки"""
        self.send_button.setEnabled(True)
        self.input_field.setEnabled(True)
        self.status_label.setText(f"❌ Ошибка: {error}")
        self.add_message("system", f"Произошла ошибка: {error}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Современный стиль
    
    window = ChatWindow()
    window.show()
    
    sys.exit(app.exec())