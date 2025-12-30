import PyInstaller.__main__

# Define o nome do executável final
exe_name = "SupervisorIndustrial"

PyInstaller.__main__.run([
    'run.py',                                   # Script orquestrador
    '--name=%s' % exe_name,
    '--onefile',                                # Gera apenas um arquivo .exe
    '--console',                                # Mantém o console aberto para ver os logs
    '--add-data=config/settings.toml;config',  # Inclui o TOML
    # Garante que as rotas sejam encontradas
    '--collect-all=fastapi',
    '--collect-all=uvicorn',
])
