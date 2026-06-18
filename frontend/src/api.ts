const API_BASE_URL = 'http://localhost:8000/api';

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
