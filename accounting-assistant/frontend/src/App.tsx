import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedMode, setSelectedMode] = useState<'ndfl' | 'taxes'>('ndfl');
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Скролл к последнему сообщению
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Аутентификация
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth`, {
        password: password
      });
      if (response.data.status === 'authenticated') {
        setAuthenticated(true);
        setMessages([
          {
            role: 'assistant',
            content: 'Привет! Я помощник бухгалтера. Помогу тебе с проверкой НДФЛ и консультациями по налогам. 📊'
          }
        ]);
      }
    } catch (error) {
      alert('Неверный пароль');
    }
  };

  // Загрузка Excel файла
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/api/upload/excel`, formData);

      setUploadedFile(file.name);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `✅ Файл "${file.name}" загружен успешно!\n\nНайдено ${response.data.rows} строк с данными.\nКолонки: ${response.data.columns.join(', ')}`
        }
      ]);
    } catch (error) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: '❌ Ошибка при загрузке файла. Проверьте, что это Excel (.xlsx или .xls)'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Отправка сообщения
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    // Добавить сообщение пользователя
    const userMessage: Message = {
      role: 'user',
      content: inputText
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

    try {
      const endpoint = selectedMode === 'ndfl' ? '/api/chat/ndfl' : '/api/chat/taxes';

      const response = await axios.post(`${API_BASE_URL}${endpoint}`, {
        message: inputText,
        history: messages
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.content
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `❌ Ошибка: ${error.response?.data?.detail || error.message}`
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  if (!authenticated) {
    return (
      <div className="login-container">
        <div className="login-box">
          <h1>🧮 Accounting Assistant</h1>
          <p>Помощник бухгалтера для проверки НДФЛ и консультаций по налогам</p>

          <form onSubmit={handleLogin}>
            <input
              type="password"
              placeholder="Введи пароль"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoFocus
            />
            <button type="submit">Вход</button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <div className="header">
        <h1>🧮 Accounting Assistant</h1>
        <div className="mode-selector">
          <button
            className={`mode-btn ${selectedMode === 'ndfl' ? 'active' : ''}`}
            onClick={() => setSelectedMode('ndfl')}
          >
            💰 Проверка НДФЛ
          </button>
          <button
            className={`mode-btn ${selectedMode === 'taxes' ? 'active' : ''}`}
            onClick={() => setSelectedMode('taxes')}
          >
            📋 Консультация по налогам
          </button>
        </div>
      </div>

      <div className="messages-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content}
            </div>
          </div>
        ))}
        {loading && <div className="message assistant"><div className="loading">Загрузка...</div></div>}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        {selectedMode === 'ndfl' && (
          <div className="file-upload">
            <label htmlFor="excel-upload">
              📁 Загрузить Excel с зарплатой
            </label>
            <input
              id="excel-upload"
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileUpload}
              disabled={loading}
            />
            {uploadedFile && <span className="file-info">✅ {uploadedFile}</span>}
          </div>
        )}

        <form onSubmit={handleSendMessage}>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={
              selectedMode === 'ndfl'
                ? 'Спроси про проверку НДФЛ...'
                : 'Спроси про налоги...'
            }
            disabled={loading}
            autoFocus
          />
          <button type="submit" disabled={loading}>
            {loading ? '⏳' : '➤'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
