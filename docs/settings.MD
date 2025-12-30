# Configurações de ambiente mínimas

As configurações de ambiente são realizadas no arquivo [settings.toml](../config/settings.toml).

## Estrutura do arquivo settings.toml:

```toml
[global]
DATABASE_URL = '' # (Obrigatória) banco local
# ... configurações para ambos ambientes (oberserver e api)

[observer]
[[observer.checkweighers]] # Repetir para cada dispositivo a ser monitorado
name = ""
ip_address = ""
port = 502
cw_id = "" # Não aleterar depois de cadastrado 1 vez
enabled = true # Habilita o monioramento
# timeout = 5.0 # (optional)
# poll_interval = 0.1 # (optional)

# ... configurações para o ambiente oberserver

[api]
port=8000 # Porta do servidor que a api responderá
host="0.0.0.0"

# ... configurações para o ambiente api

```
