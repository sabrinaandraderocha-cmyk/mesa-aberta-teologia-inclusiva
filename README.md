# Mesa Aberta - Teologia Inclusiva (Flask local)

App simples de Perguntas & Respostas no estilo "EthosPsi", adaptado para Teologia Inclusiva.

# Mesa Aberta - Teologia Inclusiva (Flask local)
- Python 3.10+ (recomendado)

# Mesa Aberta - Teologia Inclusiva (Flask local)
No terminal, dentro da pasta do projeto:

# Mesa Aberta - Teologia Inclusiva (Flask local)
Windows:
```
python -m venv .venv
.venv\Scripts\activate
```

Mac/Linux:
```
python -m venv .venv
source .venv/bin/activate
```

# Mesa Aberta - Teologia Inclusiva (Flask local)
```
pip install flask
```

# Mesa Aberta - Teologia Inclusiva (Flask local)
```
python app.py
```

Abra no navegador: http://127.0.0.1:5000

# Mesa Aberta - Teologia Inclusiva (Flask local)
- O app grava um log de perguntas em `data/ethos_teo_inclusiva.sqlite3` (tabela `query_log`).
- Para adicionar perguntas/respostas: edite `QUICK_QUESTIONS` e `RESPOSTAS_DB` no `app.py`.


# Mesa Aberta - Teologia Inclusiva (Flask local)
A página inicial inclui cartões com: denúncias (Disque 100 / SaferNet), ajuda espiritual (igrejas inclusivas) e ajuda psicológica (CVV 188 e clínicas-escola).
