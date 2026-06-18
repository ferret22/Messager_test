import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';

import { getChats, getMe, getMessages, initCsrf, login, readAllMessages } from './api';
import type { Chat, Message } from './api';

type User = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
};

function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isMessagesLoading, setIsMessagesLoading] = useState(false);
  const [username, setUsername] = useState('alice');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [messageText, setMessageText] = useState('');
  const [typingUsername, setTypingUsername] = useState<string | null>(null);
  const [typingTimeoutId, setTypingTimeoutId] = useState<number | null>(null);

  useEffect(() => {
    if (!selectedChatId || !currentUser) {
      return;
    }

    setTypingUsername(null);

    const ws = new WebSocket(`ws://localhost:8000/ws/chats/${selectedChatId}/`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'typing') {
        setTypingUsername(data.typing.is_typing ? data.typing.username : null);
      }

      if (data.type === 'message_created') {
        const message = {
          ...data.message,
          is_own: data.message.sender === currentUser.id,
          edited_at: data.message.edited_at ?? null,
        };

        setMessages((currentMessages) => [...currentMessages, message]);
        moveChatToTopWithMessage(message.chat_id ?? selectedChatId, message);
      }

      if (data.type === 'read_updated') {
        if (data.read.user === currentUser.id) {
          setChats((currentChats) =>
            currentChats.map((chat) =>
              chat.id === data.read.chat_id
                ? { ...chat, unread_count: 0 }
                : chat,
            ),
          );
        }
      }
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code);
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [selectedChatId, currentUser]);

  useEffect(() => {
    async function bootstrap() {
      try {
        await initCsrf();

        const user = await getMe();
        setCurrentUser(user);

        if (user) {
          const chatList = await getChats();
          setChats(chatList);
          setSelectedChatId(chatList[0]?.id ?? null);
        }
      } catch (error) {
        console.error('Bootstrap failed:', error);
        setError('Не удалось подключиться к серверу');
      } finally {
        setIsLoading(false);
      }
    }

    bootstrap();
  }, []);

  useEffect(() => {
    if (!selectedChatId) {
      setMessages([]);
      return;
    }

    async function loadMessages() {
      try {
        setIsMessagesLoading(true);
        const messageList = await getMessages(selectedChatId);
        setMessages(messageList);

        if (messageList.length > 0) {
          await readAllMessages(selectedChatId);

          setChats((currentChats) =>
            currentChats.map((chat) =>
              chat.id === selectedChatId
                ? { ...chat, unread_count: 0 }
                : chat,
            ),
          );
        }
      } catch (error) {
        console.error('Messages loading failed:', error);
        setMessages([]);
      } finally {
        setIsMessagesLoading(false);
      }
    }

    loadMessages();
  }, [selectedChatId]);

  function handleSendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const text = messageText.trim();

    if (!text || !socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }

    socket.send(JSON.stringify({ text }));
    setMessageText('');
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');

    try {
      const user = await login(username, password);
      setCurrentUser(user);

      const chatList = await getChats();
      setChats(chatList);
      setSelectedChatId(chatList[0]?.id ?? null);
    } catch {
      setError('Неверный логин или пароль');
    }
  }

  if (isLoading) {
    return <div className="app-shell">Загрузка...</div>;
  }

  if (currentUser) {
    const selectedChat = chats.find((chat) => chat.id === selectedChatId) ?? null;

    return (
      <div className="messenger-shell">
        <aside className="sidebar">
          <div className="sidebar-header">
            <div>
              <h1>Messenger</h1>
              <span>{currentUser.username}</span>
            </div>
          </div>

          <div className="chat-list">
            {chats.map((chat) => (
              <button
                className={`chat-item ${chat.id === selectedChatId ? 'active' : ''}`}
                key={chat.id}
                type="button"
                onClick={() => setSelectedChatId(chat.id)}
              >
                <div className="chat-avatar">
                  {chat.display_title.slice(0, 1).toUpperCase()}
                </div>

                <div className="chat-info">
                  <div className="chat-row">
                    <strong>{chat.display_title}</strong>
                    {chat.unread_count > 0 && (
                      <span className="badge">{chat.unread_count}</span>
                    )}
                  </div>

                  <p>
                    {chat.last_message
                      ? chat.last_message.text
                      : `${chat.participants_count} participants`}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </aside>

        <main className="chat-panel">
          {selectedChat ? (
            <>
              <header className="chat-header">
                <div>
                  <h2>{selectedChat.display_title}</h2>
                  <span>
                    {typingUsername
                      ? `${typingUsername} печатает...`
                      : `${selectedChat.participants_count} participants`}
                  </span>
                </div>
              </header>

              <section className="message-list">
                {isMessagesLoading ? (
                  <p className="muted">Загрузка сообщений...</p>
                ) : messages.length > 0 ? (
                  messages.map((message) => (
                    <div
                      className={`message-bubble ${message.is_own ? 'own' : ''}`}
                      key={message.id}
                    >
                      {!message.is_own && (
                        <span className="message-author">{message.sender_username}</span>
                      )}
                      <p>{message.text}</p>
                      <time>
                        {new Date(message.created_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </time>
                    </div>
                  ))
                ) : (
                  <p className="muted">Сообщений пока нет.</p>
                )}
              </section>

              <form className="message-composer" onSubmit={handleSendMessage}>
                <input
                  value={messageText}
                  onChange={(event) => {
                    setMessageText(event.target.value);
                    sendTypingStatus(true);

                    if (typingTimeoutId !== null) {
                      window.clearTimeout(typingTimeoutId);
                    }

                    const timeoutId = window.setTimeout(() => {
                      sendTypingStatus(false);
                    }, 1200);

                    setTypingTimeoutId(timeoutId);
                  }}
                  placeholder="Написать сообщение..."
                />
                <button type="submit">Отправить</button>
              </form>
            </>
          ) : (
            <section className="empty-chat">
              <p>Выберите чат.</p>
            </section>
          )}
        </main>
      </div>
    );
  }

  function moveChatToTopWithMessage(chatId: number, message: Message) {
    setChats((currentChats) => {
      const chat = currentChats.find((item) => item.id === chatId);

      if (!chat) {
        return currentChats;
      }

      const updatedChat = {
        ...chat,
        last_message: message,
        unread_count:
          chatId === selectedChatId || message.is_own
            ? chat.unread_count
            : chat.unread_count + 1,
      };

      return [
        updatedChat,
        ...currentChats.filter((item) => item.id !== chatId),
      ];
    });
  }

  function sendTypingStatus(isTyping: boolean) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }

    socket.send(JSON.stringify({
      type: 'typing',
      is_typing: isTyping,
    }));
  }

  return (
    <div className="app-shell">
      <section className="login-panel">
        <h1>Messenger</h1>
        <form onSubmit={handleSubmit}>
          <label>
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
            />
          </label>

          {error && <p className="error">{error}</p>}

          <button type="submit">Войти</button>
        </form>
      </section>
    </div>
  );
}

export default App;