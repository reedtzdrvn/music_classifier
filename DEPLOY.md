# CI/CD — автодеплой на сервер

При каждом пуше в ветку `main` GitHub Actions (`.github/workflows/deploy.yml`)
по SSH заходит на сервер, обновляет код и веса моделей (Git LFS), пересобирает и
перезапускает контейнеры, затем проверяет `/api/health`.

## Что должно быть на сервере (один раз)

1. Установлены **Docker** + **docker compose**, **git**, **git-lfs**.
2. Репозиторий склонирован, например в `/root/music_classifier`, и веса подтянуты:
   ```bash
   cd /root/music_classifier
   git lfs install
   git lfs pull
   ```
3. SSH-порт сервера доступен из интернета (GitHub-раннеры подключаются снаружи).
   Если сервер за NAT/файрволом — см. раздел «Self-hosted runner» ниже.

## Ключ для деплоя

Сгенерируй отдельную пару ключей (без пароля) — например, на сервере:

```bash
ssh-keygen -t ed25519 -f ~/deploy_key -N ""
cat ~/deploy_key.pub >> ~/.ssh/authorized_keys   # разрешаем вход этим ключом
cat ~/deploy_key                                 # это приватный ключ -> в секрет SSH_KEY
```

## Секреты репозитория

GitHub → репозиторий → **Settings → Secrets and variables → Actions → New repository secret**:

| Секрет | Значение | Пример |
|--------|----------|--------|
| `SSH_HOST` | IP или домен сервера | `203.0.113.10` |
| `SSH_USER` | пользователь SSH | `root` |
| `SSH_KEY` | **приватный** ключ целиком (содержимое `deploy_key`) | `-----BEGIN OPENSSH PRIVATE KEY----- ...` |
| `DEPLOY_PATH` | путь к репозиторию на сервере | `/root/music_classifier` |
| `SSH_PORT` | порт SSH (необязательно, по умолчанию 22) | `22` |

## Как это работает

1. `git fetch` + `git reset --hard origin/main` — приводим сервер ровно к состоянию main.
2. `git lfs pull` — дотягиваем актуальные веса моделей.
3. `docker compose up -d --build --remove-orphans` — пересобираем изменившиеся образы
   и перезапускаем контейнеры (кеш слоёв сохраняется, тяжёлый torch не качается заново).
4. `docker image prune -f` — удаляем висячие старые образы.
5. Smoke-check ждёт ответа `http://localhost:8000/api/health` до 3 минут; если сервис
   не поднялся — джоба падает и печатает логи `inference`.

Запустить деплой вручную (без пуша): вкладка **Actions → Deploy → Run workflow**.

## Self-hosted runner (если сервер недоступен снаружи)

Если к серверу нельзя подключиться по SSH из интернета, установи на нём self-hosted
runner (GitHub → Settings → Actions → Runners → New self-hosted runner) и замени в
`deploy.yml` `runs-on: ubuntu-latest` на `runs-on: self-hosted`, а шаги SSH — на
локальные команды (`cd $DEPLOY_PATH && git ... && docker compose ...`), т.к. раннер
уже работает на самом сервере.
```yaml
jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - run: |
          cd /root/music_classifier
          git fetch --all --prune && git reset --hard origin/main
          git lfs pull
          docker compose up -d --build --remove-orphans
```
