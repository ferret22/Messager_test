import { FormEvent, useEffect, useState } from 'react';

import { getMe, initCsrf, login } from './api';

type User = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
};

function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [username, setUsername] = useState('alice');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function bootstrap() {
      await initCsrf();

      const user = await getMe();
      setCurrentUser(user);
      setIsLoading(false);
    }

    bootstrap();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');

    try {
      const user = await login(username, password);
      setCurrentUser(user);
    } catch {
      setError('Неверный логин или пароль');
    }
  }

  if (isLoading) {
    return <div className="app-shell">Загрузка...</div>;
  }

  if (currentUser) {
    return (
      <div className="app-shell">
        <section className="panel">
          <h1>Messenger</h1>
          <p>Вы вошли как {currentUser.username}</p>
        </section>
      </div>
    );
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
