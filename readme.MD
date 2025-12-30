# Supervisor Modbus 🚀

Sistema de monitoramento industrial de alta performance desenvolvido em Python, focado na coleta, bufferização e persistência de dados provenientes de redes Modbus (TCP/RTU).

Este projeto foi desenhado para suportar cargas críticas de escrita, processando mais de **2.400 operações de inserção (PUTs) por minuto** de forma estável e com baixo consumo de recursos.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.12+
- **Concorrência:** `asyncio` (Event Loop para I/O não-bloqueante)
- **Banco de Dados:** PostgreSQL
- **Driver DB:** `asyncpg` (Alta performance via protocolo binário)
- **Gerenciamento de Pacotes:** Poetry
- **Configurações:** Pydantic Settings (Gestão de `.env`)

---

## 🏗️ Arquitetura e Performance

O sistema utiliza o padrão **Produtor-Consumidor** otimizado para evitar gargalos de rede:

1.  **Reader (Produtor):** Realiza leituras assíncronas na rede Modbus e alimenta um buffer central.
2.  **Buffer (Core):** Uma fila assíncrona (`asyncio.Queue`) que implementa _backpressure_, protegendo a memória do sistema caso o banco de dados oscile.
3.  **Worker (Consumidor):** Agrupa os dados em lotes (batches) e utiliza o método `executemany` do `asyncpg`, reduzindo drasticamente o overhead de rede.
4.  **Connection Pooling:** Reutiliza conexões abertas com o PostgreSQL, eliminando a latência de novos handshakes TCP.

<img src="./docs/workflow.png" alt="workflow">

## 📂 Estrutura do Projeto

```text
├─src/
|  ├── core/                  # Lógica central (Buffer, Configurações, Logger)
|  |    ├── types/            # Definição de payloads
|  |    ├── buffer.py
|  |    ├── config.py
|  |    ├── monitor.py
|  |    └── logger.py
|  ├── infrastructure/        # Infraestrutura (Modbus Reader, Database Repository)
|  |    ├── database/
|  |    |      ├── connection.py
|  |    |      └── repositories.py
|  |    └── CW.py             # Modbus reader
|  ├── services/              # Orquestração (Workers e fluxo de dados)
|  |     └── worker.py
|  ├── api/                   # Definições de payloads e contratos de dados
|  |    ├── __init__.py
|  |    └── routes.py         # Definição das rotas de api
|  └── utils/                 # Utilitários (Superclasse EventManager, conversores)
|       ├── date.py
|       └── event_manager.py
├── run.py                    # Entrypoint da aplicação
├── api.py                    # Entrypoint da api
└── main.py                   # Entrypoint do servico
```

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.12+
- Poetry instalado
- Instância de PostgreSQL ativa

### Instalação

1. **Clone o repositório:**

   ```bash
   git clone [https://github.com/ricardoracki/supervisor_modbus.git](https://github.com/ricardoracki/supervisor_modbus.git)
   cd supervisor_modbus
   ```

2. **Instale as dependências:**

   ```bash
   poetry install
   ```

3. **Configuração do Ambiente:** Crie um arquivo .env (ou local.env) na raiz do projeto conforme o exemplo:

```
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco
```

4. **Execução:**:

```
poetry run python src/main.py
```

## 📊 Repositório e Consultas

O `PesagemRepository` oferece métodos otimizados para consultas históricas e análise de dados em tempo real:

- **Filtros Dinâmicos:** Suporte para busca por `maquina_id`, `data_pesagem` ou `classificacao`.
- **Placeholder Management:** Uso de placeholders numerados (`$1`, `$2`) para prevenir SQL Injection e permitir que o PostgreSQL otimize os planos de execução.
- **Otimização de Query:** Utiliza índices temporais e limites de busca (`LIMIT 1000`) para garantir que o sistema permaneça performático mesmo após meses de operação e milhões de registros acumulados.

---

## 📄 Licença

Este projeto está sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

**Desenvolvido por [Ricardo Racki](https://github.com/ricardoracki)**
