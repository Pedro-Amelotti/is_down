# Monitor de Status de Sistemas

Este repositório contém uma aplicação web desenvolvida com **Django 5** para acompanhar, em tempo real, a disponibilidade de uma lista de URLs organizadas por servidor. A interface web atualiza automaticamente os status consultando endpoints REST internos e apresenta filtros por servidor, busca por nome e destaques visuais para cada situação (UP, DOWN, FORBIDDEN).

## Visão geral da arquitetura

- **Backend Django**: expõe os endpoints `systems_list/` (lista os sistemas configurados) e `system_status/` (consulta o status HTTP de uma URL específica).
- **Banco de dados SQLite**: persiste os modelos `Server` e `System`, relacionando sistemas a seus respectivos servidores.
- **Frontend estático**: utiliza HTML/CSS/JavaScript para construir dinamicamente os cartões de status e atualizá-los a cada 60 segundos.

A aplicação já acompanha um banco `db.sqlite3` vazio. Caso prefira começar do zero, basta excluir o arquivo antes de executar as migrações.

## Requisitos

| Ferramenta | Versão recomendada | Observações |
| ---------- | ------------------ | ----------- |
| Python     | 3.10 ou superior   | Django 5.1 requer Python 3.10+ |
| pip        | 22+                | Instalador de pacotes Python |
| Virtualenv | (opcional, mas recomendado) | Para isolar as dependências |
| Git        | Qualquer versão recente | Para clonar o projeto |

> **Obs.:** SQLite já vem incluído com o Python padrão, então não há dependência adicional de banco de dados para desenvolvimento.

## Passo a passo de instalação

1. **Clone o repositório**
   ```bash
   git clone https://github.com/Pedro-Amelotti/is_down.git
   cd is_down/status_monitor
   ```

2. **Crie (opcional) e ative um ambiente virtual**

   Linux/macOS:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   Windows (PowerShell):
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Instale as dependências do projeto**
   ```bash
   pip install "Django>=5.1,<6" "requests>=2.31,<3"
   ```

4. **Aplique as migrações do banco de dados**
   ```bash
   python manage.py migrate
   ```

5. **(Opcional, mas recomendado) Crie um superusuário para acessar o Django Admin**
   ```bash
   python manage.py createsuperuser
   ```

   Siga as instruções do prompt para definir usuário, e-mail e senha. O painel administrativo ficará disponível em `http://127.0.0.1:8000/admin/`.

## Populando servidores e sistemas para monitoramento

Existem duas formas principais de cadastrar os sistemas que serão monitorados:

1. **Via Django Admin**
   - Acesse `http://127.0.0.1:8000/admin/` com o superusuário criado.
   - Cadastre primeiro os servidores (`Server`).
   - Para cada servidor, cadastre os sistemas (`System`) informando nome e URL completa.

2. **Via shell do Django** (útil para inserir vários registros rapidamente)
   ```bash
   python manage.py shell
   ```
   ```python
   from monitor.models import Server, System

   server = Server.objects.create(name="servidor-principal")
   System.objects.create(name="Meu Site", url="https://exemplo.com", server=server)
   exit()
   ```

Após cadastrar os sistemas, a interface principal passará a exibi-los automaticamente.

## Executando o servidor de desenvolvimento

```bash
python manage.py runserver 0.0.0.0:8000
```

- A aplicação ficará disponível em `http://127.0.0.1:8000/`.
- A página principal (`/`) carrega todos os servidores e sistemas cadastrados e atualiza os status a cada 60 segundos.
- O endpoint `/system_status/` é acessado pelo JavaScript para verificar o status HTTP de cada URL. Ele retorna JSON no formato:
  ```json
  {
    "name": "Meu Site",
    "url": "https://exemplo.com",
    "status": "UP",
    "checked_at": "2024-01-01 12:00:00"
  }
  ```
- O endpoint `/systems_list/` retorna todos os servidores e seus sistemas cadastrados.

Para parar o servidor, pressione `Ctrl + C` no terminal.

## Notificações no Discord

O monitor pode enviar alertas para um canal do Discord sempre que um sistema apresentar status **DOWN** ou **FORBIDDEN**, além de
uma mensagem de recuperação quando voltar para **UP**. Para habilitar essa integração:

1. Crie (ou copie) um webhook no canal desejado seguindo as instruções da [documentação do Discord](https://support.discord.com/hc/pt-br/articles/228383668-Introdu%C3%A7%C3%A3o-aos-Webhooks).
2. Defina a URL do webhook usando um arquivo `.env` na raiz do projeto Django (`status_monitor/.env`). Você pode copiar o modelo [`status_monitor/.env.example`](status_monitor/.env.example) e atualizar o valor da variável:
   ```dotenv
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxxxxx
   ```
   O projeto carrega esse arquivo automaticamente na inicialização. Se preferir, você pode exportar a variável diretamente no terminal antes de iniciar o servidor Django:
   ```bash
   export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/xxxxxxxx"
   python manage.py runserver 0.0.0.0:8000
   ```
   No Windows (PowerShell), utilize:
   ```powershell
   $env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/xxxxxxxx"
   python manage.py runserver 0.0.0.0:8000
   ```

Com a variável definida (via `.env` ou ambiente), o backend enviará uma única notificação a cada mudança de estado (queda ou recuperação) para cada sistema monitorado.

## Estrutura do projeto

```
status_monitor/
├── manage.py
├── db.sqlite3
├── monitor/
│   ├── admin.py          # Cadastro de Server/System no admin
│   ├── models.py         # Modelos Server e System
│   ├── views.py          # Endpoints systems_list e system_status
│   ├── urls.py           # Rotas do app
│   ├── static/
│   │   ├── scripts.js    # Atualiza status periodicamente
│   │   └── styles.css    # Estilos da interface
│   └── templates/
│       └── monitor/
│           └── index.html
└── status_monitor/
    ├── settings.py
    ├── urls.py
    └── ...
```

## Testes automatizados

Até o momento não há testes automatizados implementados (`monitor/tests.py` está vazio). Você pode executar a suíte padrão do Django com:
```bash
python manage.py test
```

## Dicas e próximos passos

- Ajuste o intervalo de atualização alterando o valor passado a `setInterval` no arquivo `monitor/static/scripts.js` (valor padrão: 60000 ms).
- Para hospedar em produção, lembre-se de configurar `DEBUG = False`, definir `ALLOWED_HOSTS` corretamente e utilizar um servidor de aplicação apropriado (Gunicorn, uWSGI, etc.).
- Considere criar um arquivo `requirements.txt` ou `pyproject.toml` caso deseje fixar versões específicas das dependências.
- Consulte também o arquivo [`IMPROVEMENTS.md`](IMPROVEMENTS.md) para uma lista priorizável de melhorias sugeridas para a evolução do monitor.

Com esses passos, você terá o ambiente configurado e pronto para monitorar a disponibilidade dos seus sistemas.
