### Рекомендуемая схема запуска для проверки (из корня репозитория):

Открыть терминалы в количестве `1 (для сервера) + желаемое число клиентов`

- Терминал сервера:
  - `python3 server.py`
  - В терминале сервера будут выводиться логи (кто подключился / кто отключился). Логи соответствуют уведомлениям о подключившихся / отключившихся игроках на клиентах
- Терминал клиента:
  - `python3 client.py`
  - Сначала необходимо ввести желаемый ник игрока
  - Дальнейшая работа клиентов основана на вводе в терминал комманд `PLAYERS` / `REFRESH` / `QUIT` (регистр важен)
  - `PLAYERS` - текущий список подключенных игроков
  - `REFRESH` - вывести уведомления, накопившиеся с предыдущего запроса REFRESH
  - `QUIT` - выйти из игры (потребуется ввести ник игрока для подтверждения)

### Запуск с использованием контейнеров (из корня репозитория):

```
docker compose build
docker compose up -d
```
