# Monitor de Status de Sistemas

Essa é uma aplicação Django para monitorar os status de sites

## Instalação

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/Pedro-Amelotti/is_down
    cd status_monitor
    ```

2.  **Instale as dependências:**
    ```bash
    pip install django requests
    ```

3.  **Rode as migrações da database:**
    ```bash
    python manage.py migrate
    ```

## Rodando o servidor

Para iniciar o servidor de desenvolvimento, rode:
```bash
python manage.py runserver
```

A aplicação estará disponível em `http://127.0.0.1:8000/` ou outro ip local.
