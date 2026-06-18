const API_BASE_URL = 'http://localhost:8000/api';

export type Message = {
  id: number;
  chat_id?: number;
  sender: number;
  sender_username: string;
  is_own: boolean;
  text: string;
  created_at: string;
  edited_at: string | null;
};

export type Chat = {
  id: number;
  title: string;
  display_title: string;
  chat_type: 'private' | 'group';
  participants_count: number;
  created_at: string;
  unread_count: number;
  last_message: Message | null;
};

function getCookie(name: string): string {
    const cookies = document.cookie.split('; ');
    const cookie = cookies.find((item) => item.startsWith(`${name}=`));

    if (!cookie) {
        return '';
    }
    return decodeURIComponent(cookie.split('=')[1]);
}

export async function initCsrf(): Promise<void> {
    await fetch(`${API_BASE_URL}/auth/csrf/`, {
        credentials: 'include',
    });
}

export async function login(username: string, password: string) {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            username,
            password,
        }),
    });

    if (!response.ok) {
        throw new Error('Invalid username or password');
    }
    return response.json();
}

export async function getMe() {
    const response = await fetch(`${API_BASE_URL}/me/`, {
        credentials: 'include',
    });
    if (!response.ok) {
        return null;
    }
    return response.json();
}

export async function getChats(): Promise<Chat[]> {
  const response = await fetch(`${API_BASE_URL}/chats/`, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to load chats');
  }

  return response.json();
}

export async function getMessages(chatId: number): Promise<Message[]> {
  const response = await fetch(`${API_BASE_URL}/chats/${chatId}/messages/`, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to load messages');
  }

  return response.json();
}

export async function readAllMessages(chatId: number) {
  const response = await fetch(`${API_BASE_URL}/chats/${chatId}/read-all/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({}),
  });

  if (!response.ok) {
    throw new Error('Failed to mark chat as read');
  }

  return response.json();
}
