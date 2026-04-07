#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S  v6.0  —  Assistente Pessoal do Henrique
──────────────────────────────────────────────────────
Para ativar a IA, configure a variável de ambiente:
  Windows : set CLAUDE_API_KEY=sk-ant-...
  Linux   : export CLAUDE_API_KEY=sk-ant-...
  Pydroid : edite a linha API_KEY abaixo (só se não tiver como usar env)
"""

import sys
import os
import json
import datetime
import threading
import time
import webbrowser
import random
import math
import re

# ── imports opcionais ──────────────────────────────────────────
try:    from gtts import gTTS
except ImportError: gTTS = None

try:    import pyttsx3
except ImportError: pyttsx3 = None

try:    import requests
except ImportError: requests = None

# ══════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════
API_KEY   = os.getenv("CLAUDE_API_KEY", "")   # ← cole aqui só no Android sem env
NOME      = "Henrique"

ARQUIVO_MEM        = os.path.expanduser("~/jarvis_memoria.json")
ARQUIVO_TASKS      = os.path.expanduser("~/jarvis_tasks.json")
ARQUIVO_PENSAMENTOS= os.path.expanduser("~/jarvis_pensamentos.json")
ARQUIVO_HISTORICO  = os.path.expanduser("~/jarvis_historico.json")

CATEGORIAS = ["pessoal", "loja", "igreja"]

# ══════════════════════════════════════════════════════════════
#  DETECÇÃO DE PLATAFORMA
# ══════════════════════════════════════════════════════════════
def detectar_plataforma():
    if os.path.exists("/data/data/com.termux"):
        return "termux"
    if "ANDROID_ROOT" in os.environ or os.path.exists("/sdcard"):
        return "android"
    if sys.platform == "win32":
        return "windows"
    return "linux"

PLATAFORMA = detectar_plataforma()
ANDROID    = PLATAFORMA in ("termux", "android")
TEM_GUI    = ANDROID

# ══════════════════════════════════════════════════════════════
#  VERSÍCULOS
# ══════════════════════════════════════════════════════════════
VERSICULOS = [
    ("João 3:16",       "Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito."),
    ("Filipenses 4:13", "Tudo posso naquele que me fortalece."),
    ("Romanos 8:28",    "Sabemos que todas as coisas cooperam para o bem daqueles que amam a Deus."),
    ("Salmos 23:1",     "O Senhor é o meu pastor e nada me faltará."),
    ("Provérbios 3:5",  "Confie no Senhor de todo o seu coração e não se apoie em seu próprio entendimento."),
    ("Isaías 41:10",    "Não temas, porque eu sou contigo; não te assombres, porque eu sou o teu Deus."),
    ("Jeremias 29:11",  "Porque eu sei os planos que tenho para vocês — planos de prosperidade e não de calamidade."),
    ("Mateus 6:33",     "Buscai primeiro o Reino de Deus e a sua justiça, e todas essas coisas vos serão acrescentadas."),
    ("Romanos 5:8",     "Mas Deus demonstra seu amor: Cristo morreu em nosso favor quando ainda éramos pecadores."),
    ("Salmos 46:1",     "Deus é o nosso refúgio e fortaleza, socorro bem presente nas tribulações."),
    ("2 Timóteo 1:7",   "Porque Deus não nos deu espírito de covardia, mas de poder, de amor e de equilíbrio."),
    ("Gálatas 2:20",    "Já não sou eu quem vive, mas Cristo vive em mim."),
]

def versiculo_do_dia():
    idx = datetime.date.today().toordinal() % len(VERSICULOS)
    ref, txt = VERSICULOS[idx]
    return ref, txt

def versiculo_aleatorio():
    ref, txt = random.choice(VERSICULOS)
    return ref, txt

# ══════════════════════════════════════════════════════════════
#  CORES (terminal)
# ══════════════════════════════════════════════════════════════
class Cor:
    RESET  = "\033[0m"
    CIANO  = "\033[96m"
    VERDE  = "\033[92m"
    AMARELO= "\033[93m"
    AZUL   = "\033[94m"
    ROXO   = "\033[95m"
    BRANCO = "\033[97m"
    CINZA  = "\033[90m"
    VERMELHO="\033[91m"
    DIM    = "\033[2m"

# ══════════════════════════════════════════════════════════════
#  PERSISTÊNCIA — THREAD-SAFE
# ══════════════════════════════════════════════════════════════
_memoria_lock     = threading.Lock()
_tasks_lock       = threading.Lock()
_pensamentos_lock = threading.Lock()
_lembretes_lock   = threading.Lock()
_historico_lock   = threading.Lock()

def _carregar_json(arq, padrao):
    try:
        if os.path.exists(arq):
            with open(arq, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[Erro ao carregar {arq}] {e}")
    return padrao

def _salvar_json(arq, dados):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(arq)), exist_ok=True)
        with open(arq, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Erro ao salvar {arq}] {e}")

# Estado global
memoria      = _carregar_json(ARQUIVO_MEM,        {"loja": [], "igreja": [], "pessoal": []})
tasks        = _carregar_json(ARQUIVO_TASKS,       {"loja": [], "igreja": [], "pessoal": []})
pensamentos  = _carregar_json(ARQUIVO_PENSAMENTOS, [])
historico_ia = []
lembretes    = []

# ══════════════════════════════════════════════════════════════
#  MÓDULO — MEMÓRIA (notas rápidas)
# ══════════════════════════════════════════════════════════════
def adicionar_memoria(texto):
    with _memoria_lock:
        cat = "pessoal"
        if not isinstance(memoria.get("pessoal"), list):
            memoria["pessoal"] = []
        entrada = {
            "texto": texto,
            "hora":  datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
        memoria["pessoal"].append(entrada)
        _salvar_json(ARQUIVO_MEM, memoria)
    return entrada

def buscar_memoria(query):
    with _memoria_lock:
        q = query.lower()
        resultado = []
        for cat, itens in memoria.items():
            for item in itens:
                if q in item.get("texto","").lower():
                    resultado.append(f"[{cat}] {item['hora']} — {item['texto']}")
    return resultado

def listar_memoria_recente(n=5):
    with _memoria_lock:
        todas = []
        for cat, itens in memoria.items():
            for item in itens:
                todas.append((item.get("hora",""), cat, item.get("texto","")))
        todas.sort(key=lambda x: x[0], reverse=True)
    return todas[:n]

# ══════════════════════════════════════════════════════════════
#  MÓDULO — PENSAMENTOS / BANCO DE IDEIAS
# ══════════════════════════════════════════════════════════════
def extrair_tags(texto):
    palavras = re.findall(r'\b\w{4,}\b', texto.lower())
    stopwords = {"para","que","com","uma","uns","umas","dos","das","por",
                 "mas","mais","como","isso","esse","essa","esta","este",
                 "loja","igreja","pessoal","ideia","salva","salvar"}
    return list(set([p for p in palavras if p not in stopwords]))[:5]

def salvar_pensamento(texto, categoria="pessoal"):
    with _pensamentos_lock:
        if categoria not in CATEGORIAS:
            categoria = "pessoal"
        entrada = {
            "id":        len(pensamentos) + 1,
            "texto":     texto,
            "categoria": categoria,
            "hora":      datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            "tags":      extrair_tags(texto),
        }
        pensamentos.append(entrada)
        _salvar_json(ARQUIVO_PENSAMENTOS, pensamentos)
    return entrada

def buscar_pensamentos(query, categoria=None):
    with _pensamentos_lock:
        q = query.lower()
        resultado = []
        for p in pensamentos:
            match_texto = q in p["texto"].lower()
            match_cat   = (categoria is None) or (p["categoria"] == categoria)
            match_tag   = any(q in tag for tag in p.get("tags",[]))
            if match_cat and (match_texto or match_tag or q == ""):
                resultado.append(p)
    return resultado

def conectar_ideias():
    with _pensamentos_lock:
        if len(pensamentos) < 2:
            return {}
        tags_map = {}
        for p in pensamentos:
            for tag in p.get("tags", []):
                if tag not in tags_map:
                    tags_map[tag] = []
                tags_map[tag].append(p["texto"][:60])
        return {t: v for t, v in tags_map.items() if len(v) > 1}

# ══════════════════════════════════════════════════════════════
#  MÓDULO — TAREFAS
# ══════════════════════════════════════════════════════════════
def _proximo_id():
    with _tasks_lock:
        maior = 0
        for itens in tasks.values():
            for t in itens:
                if t.get("id", 0) > maior:
                    maior = t["id"]
    return maior + 1

def salvar_task(texto, categoria="pessoal"):
    with _tasks_lock:
        categoria = categoria.lower()
        if categoria not in tasks:
            tasks[categoria] = []
        tarefa = {
            "id":    _proximo_id(),
            "texto": texto,
            "feito": False,
            "hora":  datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
        tasks[categoria].append(tarefa)
        _salvar_json(ARQUIVO_TASKS, tasks)
    return tarefa

def listar_tasks(categoria=None):
    with _tasks_lock:
        resultado = []
        cats = [categoria] if categoria else list(tasks.keys())
        for cat in cats:
            for t in tasks.get(cat, []):
                if not t["feito"]:
                    resultado.append((t["id"], cat, t["texto"]))
    return resultado

def concluir_task(id_tarefa):
    with _tasks_lock:
        for cat_itens in tasks.values():
            for t in cat_itens:
                if t.get("id") == id_tarefa:
                    t["feito"] = True
                    _salvar_json(ARQUIVO_TASKS, tasks)
                    return t
    return None

# ══════════════════════════════════════════════════════════════
#  LEMBRETES
# ══════════════════════════════════════════════════════════════
def agendar_lembrete(descricao, segundos, callback=None):
    def disparar():
        time.sleep(segundos)
        msg = f"Lembrete: {descricao}"
        if callback:
            callback(f"🔔 {msg}")
        else:
            falar(msg, async_=False)
        if PLATAFORMA == "termux":
            os.system(f'termux-notification --title "JARVIS" --content "{msg}"')
        if PLATAFORMA == "windows":
            try:
                import winsound
                for _ in range(3):
                    winsound.Beep(1000, 300)
                    time.sleep(0.1)
            except Exception:
                pass
    threading.Thread(target=disparar, daemon=True).start()
    with _lembretes_lock:
        lembretes.append({
            "descricao": descricao,
            "segundos":  segundos,
            "criado":    datetime.datetime.now().isoformat()
        })

# ══════════════════════════════════════════════════════════════
#  PARSE DE LEMBRETE
# ══════════════════════════════════════════════════════════════
IGNORAR_LEMBRETE = {
    "em","de","me","lembra","lembrete","avisa","por","favor",
    "o","a","um","uma","às","as","ao","para","pra","lembrar","que"
}

def _extrair_desc(palavras, excluir):
    return " ".join(w for w in palavras
                    if w not in IGNORAR_LEMBRETE and w not in excluir)

def parse_lembrete(cmd):
    agora    = datetime.datetime.now()
    palavras = cmd.lower().split()
    segundos = None
    recorrente = None

    # "em instantes" / "daqui a pouco"
    if any(p in cmd for p in ["em instantes","daqui a pouco","agora pouco"]):
        desc = _extrair_desc(palavras, {"instantes","daqui","pouco","agora"})
        return desc or "tarefa", 60, None

    # "em X minutos/horas/segundos"
    for i, p in enumerate(palavras):
        mult = None
        if p in ["minuto","minutos"]:     mult = 60
        elif p in ["hora","horas"]:       mult = 3600
        elif p in ["segundo","segundos"]: mult = 1
        if mult:
            try:
                n = int(palavras[i - 1])
                segundos = n * mult
                desc = _extrair_desc(palavras, {str(n), p})
                return desc or "tarefa", segundos, None
            except (ValueError, IndexError):
                pass

    # "às 15h" / "às 14:30" / "amanhã às 9h" / "toda segunda às 8h"
    m = re.search(r'(?:às?|as)\s*(\d{1,2})(?::(\d{2}))?h?', cmd)
    if m:
        hora_alvo = int(m.group(1))
        min_alvo  = int(m.group(2)) if m.group(2) else 0

        dias_semana = {
            "segunda":0,"terça":1,"terca":1,"quarta":2,
            "quinta":3,"sexta":4,"sábado":5,"sabado":5,"domingo":6
        }
        dia_rec = None
        for nome_dia, num_dia in dias_semana.items():
            if nome_dia in cmd:
                dia_rec = num_dia
                recorrente = nome_dia
                break

        base = agora
        if "amanhã" in cmd or "amanha" in cmd:
            base = agora + datetime.timedelta(days=1)
        elif dia_rec is not None:
            dias_ate = (dia_rec - agora.weekday()) % 7
            if dias_ate == 0 and (hora_alvo < agora.hour or
               (hora_alvo == agora.hour and min_alvo <= agora.minute)):
                dias_ate = 7
            base = agora + datetime.timedelta(days=dias_ate)

        alvo = base.replace(hour=hora_alvo, minute=min_alvo, second=0, microsecond=0)
        if alvo <= agora and "amanhã" not in cmd and "amanha" not in cmd and dia_rec is None:
            alvo += datetime.timedelta(days=1)

        segundos = int((alvo - agora).total_seconds())
        excluir_re = set(re.findall(r'\w+', m.group(0)))
        desc = _extrair_desc(palavras, excluir_re | {"amanhã","amanha","toda","todo"})
        return desc or "tarefa", segundos, recorrente

    return "tarefa", None, None

def _tempo_str(s):
    if s >= 86400:
        d = s // 86400; h = (s % 86400) // 3600
        return f"{d}d {h}h" if h else f"{d}d"
    if s >= 3600: return f"{s//3600}h{(s%3600)//60:02d}min"
    if s >= 60:   return f"{s//60}min"
    return f"{s}s"

# ══════════════════════════════════════════════════════════════
#  VOZ
# ══════════════════════════════════════════════════════════════
VOZ_OK  = False
_engine = None
_voz_lock = threading.Lock()

def _init_voz():
    global VOZ_OK, _engine
    if PLATAFORMA == "termux":
        VOZ_OK = True; return
    if ANDROID:
        if gTTS is not None: VOZ_OK = True
        return
    if pyttsx3 is None:
        print("[Aviso] pyttsx3 não instalado. Voz desativada.")
        return
    try:
        _engine = pyttsx3.init()
        for v in _engine.getProperty('voices'):
            if 'portuguese' in v.name.lower() or 'brasil' in v.name.lower():
                _engine.setProperty('voice', v.id); break
        _engine.setProperty('rate', 165)
        _engine.setProperty('volume', 0.95)
        VOZ_OK = True
    except Exception as e:
        print(f"[Aviso] Voz desativada: {e}")

def falar(texto, async_=True):
    if not VOZ_OK:
        return
    def _f():
        with _voz_lock:
            try:
                if PLATAFORMA == "termux":
                    os.system(f'termux-tts-speak "{texto}"')
                elif ANDROID:
                    if gTTS is None:
                        print("[Erro voz] gTTS não instalado."); return
                    from playsound import playsound
                    tts = gTTS(text=texto[:300], lang='pt', slow=False)
                    arq = "/sdcard/jarvis_voz.mp3"
                    tts.save(arq); playsound(arq)
                else:
                    if _engine:
                        _engine.say(texto); _engine.runAndWait()
            except Exception as e:
                print(f"[Erro voz] {e}")
    if async_:
        threading.Thread(target=_f, daemon=True).start()
    else:
        _f()

# ══════════════════════════════════════════════════════════════
#  CLAUDE API
# ══════════════════════════════════════════════════════════════
SYSTEM_PROMPT = f"""Você é J.A.R.V.I.S — o assistente pessoal de {NOME}.

PERSONALIDADE:
- Tom casual, direto, leve humor — como um amigo muito inteligente
- Não é robótico. Fala naturalmente, como no filme Homem de Ferro
- Às vezes antecipa o que Henrique precisa antes de ele perguntar
- Pode ser levemente irônico quando faz sentido, mas nunca descortês
- Chama o usuário de "Henrique"

CONTEXTO DE HENRIQUE:
- Tem ADHD e ansiedade — ajude com clareza e direcionamento objetivo
- Trabalha na Adonai Sempre, loja evangélica em Itaperuçu-PR
- Serve na mídia/storymaker da sua igreja
- Está no 2º ano de Administração
- Faz cursos de Marketing Digital e IA
- Iniciando inglês
- Tem namorada
- Pega ônibus às 8h30, trabalha das 9h às 18h

FÉ CRISTÃ:
- Conhece a Bíblia, o evangelho, a história de Jesus
- A loja é evangélica — nunca misture com símbolos católicos
- Pode trazer versículos no momento certo
- Entende datas gospel: Páscoa, Natal, Dia do Evangélico

COMPORTAMENTO:
- Respostas curtas e objetivas (máximo 3 frases/parágrafos)
- Nunca se identifique como "IA da Anthropic" — você é J.A.R.V.I.S
- Quando Henrique estiver ansioso, seja âncora: claro, calmo, prático
"""

def perguntar_ia(pergunta, callback_ok, callback_err):
    if not API_KEY:
        callback_err("API Key não configurada. Configure CLAUDE_API_KEY.")
        return
    if requests is None:
        callback_err("'requests' não encontrado. Instale: pip install requests")
        return

    with _historico_lock:
        historico_ia.append({"role": "user", "content": pergunta})
        msgs = list(historico_ia[-12:])

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model":      "claude-sonnet-4-20250514",
                "max_tokens": 400,
                "system":     SYSTEM_PROMPT,
                "messages":   msgs,
            },
            timeout=15
        )
        resp.raise_for_status()
        resposta = resp.json()["content"][0]["text"].strip()
        with _historico_lock:
            historico_ia.append({"role": "assistant", "content": resposta})
        callback_ok(resposta)

    except requests.exceptions.ConnectionError:
        callback_err("Sem conexão com a internet.")
    except requests.exceptions.Timeout:
        callback_err("IA demorou pra responder. Tenta de novo.")
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response else "?"
        if code == 401:
            callback_err("API Key inválida.")
        elif code == 429:
            callback_err("Limite de requisições atingido. Aguarda um pouco.")
        else:
            callback_err(f"Erro HTTP {code}.")
    except Exception as e:
        callback_err(f"Erro IA: {str(e)[:80]}")

# ══════════════════════════════════════════════════════════════
#  SAUDAÇÃO
# ══════════════════════════════════════════════════════════════
def saudacao():
    hora = datetime.datetime.now().hour
    if 5 <= hora < 12:    periodo = "Bom dia"
    elif 12 <= hora < 18: periodo = "Boa tarde"
    else:                  periodo = "Boa noite"
    ia = "IA conectada." if API_KEY else "IA offline — configure CLAUDE_API_KEY quando quiser."
    return f"{periodo}, {NOME}. Sistemas online. {ia}"

# ══════════════════════════════════════════════════════════════
#  PROCESSAMENTO — NÚCLEO COMPARTILHADO
# ══════════════════════════════════════════════════════════════
def processar(cmd, responder_fn, log_fn=None, lembrete_callback=None):
    """
    Núcleo compartilhado entre terminal e GUI.
    responder_fn(texto)     → exibe resposta principal
    log_fn(texto, cor=None) → linhas extras (opcional)
    lembrete_callback(msg)  → chamado quando lembrete dispara
    Retorna False para encerrar o loop.
    """
    if log_fn is None:
        log_fn = lambda t, c=None: None

    c = cmd.lower().strip()
    if not c:
        return True

    # ── Hora ──────────────────────────────────────────────────
    if any(p in c for p in ["que horas","hora","horas"]) and "lembrete" not in c:
        agora = datetime.datetime.now()
        responder_fn(f"São {agora.hour:02d}:{agora.minute:02d}, {NOME}.")

    # ── Data ──────────────────────────────────────────────────
    elif any(p in c for p in ["que dia","data","hoje","dia da semana"]) and "lembrete" not in c:
        hoje  = datetime.datetime.now()
        dias  = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
        meses = ["janeiro","fevereiro","março","abril","maio","junho",
                 "julho","agosto","setembro","outubro","novembro","dezembro"]
        responder_fn(f"{dias[hoje.weekday()]}, {hoje.day} de {meses[hoje.month-1]} de {hoje.year}.")

    # ── Versículo ─────────────────────────────────────────────
    elif any(p in c for p in ["versículo","versiculo","palavra do dia","palavra pra hoje"]):
        if any(p in c for p in ["aleatório","aleatorio","outro","nova"]):
            ref, txt = versiculo_aleatorio()
        else:
            ref, txt = versiculo_do_dia()
        responder_fn(f"✝️  {ref}")
        log_fn(f'   "{txt}"')

    # ── Salvar ideia / pensamento ──────────────────────────────
    elif any(p in c for p in ["salvar ideia","salva ideia","guarda ideia",
                               "anotar ideia","salva pensamento","ideia:"]):
        cat = "pessoal"
        if any(p in c for p in ["loja","adonai"]): cat = "loja"
        elif any(p in c for p in ["igreja","ministério","ministerio"]): cat = "igreja"

        texto = c
        for rem in ["salvar ideia","salva ideia","guarda ideia","anotar ideia",
                    "salva pensamento","ideia:","loja","adonai","igreja",
                    "ministério","ministerio","pessoal","na categoria","categoria"]:
            texto = texto.replace(rem, "")
        texto = texto.strip(" :-,.")
        if texto:
            p = salvar_pensamento(texto, cat)
            responder_fn(f'Ideia #{p["id"]} salva em [{cat}].')
            if p["tags"]:
                log_fn(f'   Tags: {", ".join(p["tags"])}')
        else:
            responder_fn("Qual é a ideia? Me fala que eu anoto.")

    # ── Listar pensamentos ────────────────────────────────────
    elif any(p in c for p in ["minhas ideias","meus pensamentos","lista ideias"]):
        cat_filtro = None
        for cat in CATEGORIAS:
            if cat in c:
                cat_filtro = cat; break
        resultados = buscar_pensamentos("", cat_filtro)
        if not resultados:
            responder_fn("Nenhuma ideia salva ainda." + (f" [{cat_filtro}]" if cat_filtro else ""))
        else:
            label = f"[{cat_filtro}]" if cat_filtro else "todas as categorias"
            responder_fn(f"{len(resultados)} ideia(s) em {label}:")
            for p in resultados[-8:]:
                log_fn(f'   #{p["id"]} [{p["categoria"]}] {p["hora"]} — {p["texto"][:60]}')

    # ── Buscar ideia ──────────────────────────────────────────
    elif any(p in c for p in ["busca ideia","buscar ideia","procura ideia","acha ideia"]):
        termo = c
        for rem in ["busca ideia","buscar ideia","procura ideia","acha ideia"]:
            termo = termo.replace(rem, "")
        termo = termo.strip()
        if termo:
            resultados = buscar_pensamentos(termo)
            if resultados:
                responder_fn(f"{len(resultados)} resultado(s) para '{termo}':")
                for p in resultados[:5]:
                    log_fn(f'   [{p["categoria"]}] {p["hora"]} — {p["texto"][:60]}')
            else:
                responder_fn(f"Nenhuma ideia com '{termo}'.")
        else:
            responder_fn("O que você quer buscar?")

    # ── Conectar ideias ───────────────────────────────────────
    elif any(p in c for p in ["conectar ideias","conexão entre ideias","conexoes"]):
        conexoes = conectar_ideias()
        if not conexoes:
            responder_fn("Precisa de mais ideias pra eu encontrar conexões, Henrique.")
        else:
            responder_fn(f"{len(conexoes)} conexão(ões) encontrada(s):")
            for tag, itens in list(conexoes.items())[:5]:
                log_fn(f"   #{tag}")
                for item in itens:
                    log_fn(f"     → {item}...")

    # ── Adicionar tarefa ──────────────────────────────────────
    elif any(p in c for p in ["adicionar tarefa","add tarefa","nova tarefa",
                               "cria tarefa","tarefa:"]):
        cat = "pessoal"
        if any(p in c for p in ["loja","adonai"]): cat = "loja"
        elif any(p in c for p in ["igreja","ministério","ministerio"]): cat = "igreja"
        texto = c
        for rem in ["adicionar tarefa","add tarefa","nova tarefa","cria tarefa","tarefa:",
                    "loja","adonai","igreja","ministério","ministerio","pessoal"]:
            texto = texto.replace(rem, "")
        texto = texto.strip(" :-,.")
        if texto:
            t = salvar_task(texto, cat)
            responder_fn(f'Tarefa #{t["id"]} adicionada em [{cat}]: "{texto}"')
        else:
            responder_fn("Qual é a tarefa?")

    # ── Listar tarefas ────────────────────────────────────────
    elif any(p in c for p in ["minhas tarefas","listar tarefas",
                               "o que tenho pra fazer","tarefas pendentes"]):
        cat = None
        if "loja" in c or "adonai" in c: cat = "loja"
        elif "igreja" in c or "ministério" in c: cat = "igreja"
        elif "pessoal" in c: cat = "pessoal"
        pendentes = listar_tasks(cat)
        if pendentes:
            label = f"[{cat}]" if cat else "todas"
            responder_fn(f"{len(pendentes)} tarefa(s) pendente(s) — {label}:")
            for tid, tcat, ttxt in pendentes:
                log_fn(f"   #{tid} [{tcat}] {ttxt}")
        else:
            responder_fn("Nenhuma tarefa pendente." + (f" [{cat}]" if cat else " Dia livre! 🙌"))

    # ── Concluir tarefa (feita 3) ─────────────────────────────
    elif c.startswith("feita ") or c.startswith("concluir ") or c.startswith("concluída "):
        partes = c.split()
        try:
            tid = int(partes[1])
            t = concluir_task(tid)
            if t:
                responder_fn(f"Tarefa #{tid} concluída! 💪")
            else:
                responder_fn(f"Não achei a tarefa #{tid}.")
        except (IndexError, ValueError):
            responder_fn("Me fala o número da tarefa. Ex: feita 3")

    # ── Lembrar (memória rápida) ──────────────────────────────
    elif c.startswith("lembrar ") or c.startswith("anota "):
        texto = cmd.split(" ", 1)[1].strip() if " " in cmd else ""
        if texto:
            adicionar_memoria(texto)
            responder_fn("Guardado na memória.")
        else:
            responder_fn("O que você quer guardar?")

    # ── Ver memória ───────────────────────────────────────────
    elif c in ["memoria","memória","ver memoria","ver memória"]:
        recentes = listar_memoria_recente(5)
        if not recentes:
            responder_fn("Memória vazia.")
        else:
            responder_fn("Últimas 5 notas:")
            for hora, cat, txt in recentes:
                log_fn(f"   {hora} [{cat}] — {txt}")

    # ── Buscar memória ────────────────────────────────────────
    elif any(p in c for p in ["buscar memoria","busca memoria",
                               "buscar memória","busca memória"]):
        partes = c.split(None, 2)
        query  = partes[2] if len(partes) > 2 else ""
        if query:
            resultados = buscar_memoria(query)
            if resultados:
                responder_fn(f"{len(resultados)} resultado(s) na memória:")
                for r in resultados[:5]:
                    log_fn(f"   {r}")
            else:
                responder_fn(f"Nada encontrado sobre '{query}' na memória.")
        else:
            responder_fn("O que quer buscar na memória?")

    # ── Lembrete ──────────────────────────────────────────────
    elif any(p in c for p in ["lembra","lembrete","me avisa","me lembra"]):
        desc, segundos, recorrente = parse_lembrete(c)
        if segundos and segundos > 0:
            agendar_lembrete(desc, segundos, callback=lembrete_callback)
            ts = _tempo_str(segundos)
            if recorrente:
                responder_fn(f"Lembrete recorrente toda {recorrente}: \"{desc}\" em {ts}.")
            else:
                responder_fn(f"Lembrete agendado: \"{desc}\" em {ts}.")
        else:
            responder_fn('Não entendi o tempo. Ex: "me lembra de tomar água em 30 minutos" ou "às 15h reunião".')

    # ── Listar lembretes ──────────────────────────────────────
    elif any(p in c for p in ["meus lembretes","lembretes ativos","lembretes agendados"]):
        with _lembretes_lock:
            lem = list(lembretes)
        if lem:
            responder_fn(f"{len(lem)} lembrete(s) agendado(s):")
            for l in lem[:5]:
                log_fn(f'   🔔 {l["descricao"]}')
        else:
            responder_fn("Nenhum lembrete ativo.")

    # ── Abrir YouTube ─────────────────────────────────────────
    elif "youtube" in c:
        responder_fn("Abrindo o YouTube.")
        webbrowser.open("https://youtube.com")

    # ── Pesquisar ─────────────────────────────────────────────
    elif any(p in c for p in ["pesquisa","pesquisar","busca no google","buscar no google"]):
        for rem in ["pesquisa","pesquisar","busca no google","buscar no google","no google","sobre"]:
            c = c.replace(rem, "")
        termo = c.strip()
        if termo:
            responder_fn(f"Pesquisando: {termo}")
            webbrowser.open(f"https://www.google.com/search?q={termo.replace(' ','+')}")
        else:
            responder_fn("O que você quer pesquisar?")

    # ── Abrir Google ──────────────────────────────────────────
    elif "google" in c:
        responder_fn("Abrindo o Google.")
        webbrowser.open("https://google.com")

    # ── Status ────────────────────────────────────────────────
    elif any(p in c for p in ["status","sistemas","como você está","tudo bem"]):
        agora = datetime.datetime.now().strftime("%H:%M")
        with _lembretes_lock:  n_lem  = len(lembretes)
        with _tasks_lock:
            n_task = sum(len([t for t in v if not t["feito"]]) for v in tasks.values())
        with _pensamentos_lock: n_id  = len(pensamentos)
        ia_str = "IA online ✅" if API_KEY else "IA offline ⚠️"
        responder_fn(
            f"Sistemas OK | {agora} | {n_lem} lembrete(s) | "
            f"{n_task} tarefa(s) | {n_id} ideia(s) | {ia_str}"
        )

    # ── Encerrar ──────────────────────────────────────────────
    elif any(p in c for p in ["encerra","desliga","tchau","até logo","dorme","fechar","sair"]):
        responder_fn(f"Até logo, {NOME}. Que Deus te guarde. 🙏")
        return False

    # ── Limpar tela ───────────────────────────────────────────
    elif c in ["limpar","clear","cls"]:
        os.system("clear" if os.name != "nt" else "cls")
        _banner_terminal()
        return True

    # ── Ajuda ─────────────────────────────────────────────────
    elif any(p in c for p in ["ajuda","help","comandos","o que você faz"]):
        responder_fn("Comandos disponíveis:")
        ajuda = [
            "hora / data",
            "versículo  /  versículo aleatório",
            "─── IDEIAS ───",
            "salva ideia [loja|igreja|pessoal]: [texto]",
            "minhas ideias  /  minhas ideias loja",
            "busca ideia [palavra]",
            "conectar ideias",
            "─── TAREFAS ───",
            "nova tarefa [loja|igreja|pessoal]: [texto]",
            "minhas tarefas  /  minhas tarefas loja",
            "feita [número]",
            "─── MEMÓRIA ───",
            "lembrar [nota rápida]",
            "memoria  /  buscar memoria [palavra]",
            "─── LEMBRETES ───",
            "me lembra de X em 30 minutos",
            "lembrete reunião às 15h",
            "amanhã às 9h devocional",
            "toda segunda às 8h oração",
            "meus lembretes",
            "─── OUTROS ───",
            "pesquisa [termo]  /  youtube",
            "status  /  limpar  /  encerra",
            "─── IA ───",
            "[qualquer pergunta livre → vai pra IA]" if API_KEY
            else "[configure CLAUDE_API_KEY pra perguntas livres]",
        ]
        for a in ajuda:
            log_fn(f"  {a}")

    # ── IA (fallback) ─────────────────────────────────────────
    else:
        if API_KEY:
            log_fn("🧠 consultando IA...")
            def _ok(r):  responder_fn(r)
            def _err(e): responder_fn(f"⚠️ {e}")
            threading.Thread(target=perguntar_ia, args=(cmd, _ok, _err), daemon=True).start()
        else:
            responder_fn("Não entendi. Digite 'ajuda' pra ver os comandos.")
            log_fn("(Configure CLAUDE_API_KEY pra perguntas livres.)")

    return True

# ══════════════════════════════════════════════════════════════
#  INTERFACE TERMINAL
# ══════════════════════════════════════════════════════════════
def _banner_terminal():
    os.system("clear" if os.name != "nt" else "cls")
    ref, txt = versiculo_do_dia()
    ia_cor  = Cor.VERDE if API_KEY else Cor.AMARELO
    ia_info = "IA ONLINE ✅" if API_KEY else "IA OFFLINE — configure CLAUDE_API_KEY"
    print(f"""
{Cor.CIANO}╔══════════════════════════════════════════╗
║       J . A . R . V . I . S              ║
║   Assistente Pessoal — {NOME:<16}  ║
╚══════════════════════════════════════════╝{Cor.RESET}
{Cor.DIM}  Plataforma: {PLATAFORMA}  |  {ia_cor}{ia_info}{Cor.RESET}

{Cor.ROXO}  ✝️  {ref}:{Cor.RESET}
{Cor.CINZA}  "{txt}"{Cor.RESET}

{Cor.CINZA}  Digite 'ajuda' para ver os comandos.{Cor.RESET}
""")

def _ouvir_pc():
    try:
        import speech_recognition as sr
        rec = sr.Recognizer()
        rec.pause_threshold  = 1
        rec.energy_threshold = 300
        with sr.Microphone() as src:
            print(f"{Cor.DIM}[ouvindo...]{Cor.RESET}")
            rec.adjust_for_ambient_noise(src, duration=0.5)
            try:
                audio = rec.listen(src, timeout=5, phrase_time_limit=8)
            except sr.WaitTimeoutError:
                return ""
        return rec.recognize_google(audio, language='pt-BR')
    except Exception as e:
        print(f"{Cor.VERMELHO}[Erro microfone] {e}{Cor.RESET}")
        return ""

def run_terminal():
    _banner_terminal()
    sauda = saudacao()
    print(f"{Cor.CIANO}🤖 JARVIS: {sauda}{Cor.RESET}\n")
    falar(sauda)

    usar_voz = PLATAFORMA in ("windows","linux") and not ANDROID
    rodando  = True

    while rodando:
        try:
            if usar_voz:
                cmd = _ouvir_pc()
                if not cmd:
                    cmd = input(f"{Cor.AMARELO}Você: {Cor.RESET}").strip()
            else:
                cmd = input(f"{Cor.AMARELO}Você: {Cor.RESET}").strip()

            if not cmd:
                continue

            def responder(texto):
                print(f"\n{Cor.CIANO}🤖 JARVIS:{Cor.RESET} {texto}")
                falar(texto)

            def log_extra(texto, cor=None):
                print(f"{Cor.CINZA}{texto}{Cor.RESET}")

            rodando = processar(cmd, responder, log_extra)

        except KeyboardInterrupt:
            print(f"\n{Cor.CIANO}🤖 JARVIS: Até logo, {NOME}. 🙏{Cor.RESET}")
            break
        except EOFError:
            break

# ══════════════════════════════════════════════════════════════
#  INTERFACE GRÁFICA HUD (Android — Pydroid 3)
# ══════════════════════════════════════════════════════════════
def run_gui():
    try:
        import tkinter as tk
        from tkinter import simpledialog
    except ImportError:
        print("Tkinter não disponível. Rodando no terminal.")
        run_terminal(); return

    PRETO     = "#050810"
    AZUL_DEEP = "#0a1628"
    CIANO     = "#00d4ff"
    CIANO_DIM = "#004d5e"
    BRANCO    = "#e8f4fd"
    CINZA     = "#4a6080"
    VERDE     = "#00ff88"
    VERMELHO  = "#ff3355"
    AMARELO   = "#ffcc00"
    ROXO      = "#9d4edd"
    AZUL      = "#0d6efd"

    class JarvisApp:
        def __init__(self, root):
            self.root = root
            self.root.title("J.A.R.V.I.S")
            self.root.configure(bg=PRETO)
            self.root.geometry("420x860")
            self.root.resizable(False, False)
            self._angle = 0
            self._pulse = 0
            self._pulse_dir = 1
            self._build()
            self._animar()
            self.root.after(600, self._saudacao_inicial)

        def _build(self):
            # Canvas HUD
            self.canvas = tk.Canvas(self.root, width=420, height=200,
                                    bg=PRETO, highlightthickness=0)
            self.canvas.pack()

            # Badge IA
            ia_cor = VERDE if API_KEY else VERMELHO
            ia_txt = "● IA ONLINE" if API_KEY else "● IA OFFLINE — configure CLAUDE_API_KEY"
            tk.Label(self.root, text=ia_txt, font=("Courier", 9),
                     fg=ia_cor, bg=PRETO).pack(pady=(0, 4))

            # Log
            log_frame = tk.Frame(self.root, bg=AZUL_DEEP,
                                  highlightbackground=CIANO_DIM, highlightthickness=1)
            log_frame.pack(fill="x", padx=14, pady=2)
            self.log = tk.Text(log_frame, height=7, bg=AZUL_DEEP, fg=BRANCO,
                               font=("Courier", 11), relief="flat",
                               padx=10, pady=8, wrap="word", state="disabled")
            self.log.pack(fill="x")
            self.log.tag_config("c", foreground=CIANO)
            self.log.tag_config("y", foreground=AMARELO)
            self.log.tag_config("g", foreground=VERDE)
            self.log.tag_config("r", foreground=VERMELHO)
            self.log.tag_config("p", foreground=ROXO)
            self.log.tag_config("d", foreground=CINZA)

            # Botões de ação rápida
            bf = tk.Frame(self.root, bg=PRETO)
            bf.pack(fill="x", padx=14, pady=6)
            acoes = [
                ("🕐  HORA",          lambda: self._cmd("hora")),
                ("📅  DATA",          lambda: self._cmd("data")),
                ("✝️  VERSÍCULO",     lambda: self._cmd("versículo")),
                ("📋  TAREFAS",       lambda: self._cmd("minhas tarefas")),
                ("🔔  LEMBRETE",      self._dialog_lembrete),
                ("🔍  PESQUISAR",     self._dialog_pesquisa),
                ("💡  SALVAR IDEIA",  self._dialog_ideia),
                ("🔎  BUSCAR IDEIA",  self._dialog_busca),
                ("🔗  CONECTAR",      lambda: self._cmd("conectar ideias")),
                ("📌  MEMÓRIA",       lambda: self._cmd("memoria")),
            ]
            for i, (label, fn) in enumerate(acoes):
                r, col = divmod(i, 2)
                b = tk.Button(bf, text=label, font=("Courier", 11, "bold"),
                              fg=CIANO, bg=AZUL_DEEP, activeforeground=PRETO,
                              activebackground=CIANO, relief="flat", bd=0,
                              padx=8, pady=11, cursor="hand2", command=fn,
                              highlightbackground=CIANO_DIM, highlightthickness=1)
                b.grid(row=r, column=col, padx=4, pady=3, sticky="ew")
                bf.columnconfigure(col, weight=1)

            # Botão IA
            ia_bg = ROXO if API_KEY else AZUL_DEEP
            ia_fg = PRETO if API_KEY else CINZA
            tk.Button(self.root, text="🧠  PERGUNTAR À IA",
                      font=("Courier", 13, "bold"), fg=ia_fg, bg=ia_bg,
                      activeforeground=PRETO, activebackground="#7b2fbe",
                      relief="flat", bd=0, padx=10, pady=12, cursor="hand2",
                      command=self._dialog_ia,
                      highlightbackground=ROXO, highlightthickness=1
                      ).pack(fill="x", padx=14, pady=(2, 4))

            tk.Frame(self.root, bg=CIANO_DIM, height=1).pack(fill="x", padx=14, pady=2)

            # Input livre
            tk.Label(self.root, text="COMANDO LIVRE", font=("Courier", 8),
                     fg=CINZA, bg=PRETO).pack(anchor="w", padx=14, pady=(4, 2))
            row = tk.Frame(self.root, bg=PRETO)
            row.pack(fill="x", padx=14, pady=4)
            self.entry = tk.Entry(row, font=("Courier", 13), bg=AZUL_DEEP, fg=BRANCO,
                                  insertbackground=CIANO, relief="flat", bd=0,
                                  highlightbackground=CIANO_DIM, highlightthickness=1)
            self.entry.pack(side="left", fill="x", expand=True, ipady=9, padx=(0, 6))
            self.entry.bind("<Return>", self._enviar)
            tk.Button(row, text="▶", font=("Courier", 14, "bold"),
                      fg=PRETO, bg=CIANO, activebackground=AZUL,
                      relief="flat", bd=0, padx=14, pady=5,
                      cursor="hand2", command=self._enviar).pack(side="right")

            tk.Label(self.root, text=f"J.A.R.V.I.S  v6.0  •  {PLATAFORMA.upper()}",
                     font=("Courier", 8), fg=CINZA, bg=PRETO).pack(pady=(6, 3))

        def _animar(self):
            c = self.canvas; c.delete("all")
            cx, cy, r = 210, 100, 68
            for i in range(5, 0, -1):
                c.create_oval(cx-(r+i*6), cy-(r+i*6), cx+(r+i*6), cy+(r+i*6),
                              outline=f"#00{format(int(15+i*7),'02x')}ff", width=1)
            for i in range(12):
                ang = math.radians((self._angle + i * 30))
                x1=cx+(r+12)*math.cos(ang); y1=cy+(r+12)*math.sin(ang)
                x2=cx+(r+22)*math.cos(ang); y2=cy+(r+22)*math.sin(ang)
                c.create_line(x1, y1, x2, y2, fill=CIANO, width=1.5)
            c.create_oval(cx-r, cy-r, cx+r, cy+r, outline=CIANO, width=2)
            cor_arco = ROXO if API_KEY else AZUL
            c.create_arc(cx-r-8, cy-r-8, cx+r+8, cy+r+8,
                         start=self._angle*2, extent=180+self._pulse*80,
                         outline=cor_arco, width=3, style="arc")
            ri = 44+self._pulse*5
            c.create_oval(cx-ri, cy-ri, cx+ri, cy+ri, outline=CIANO_DIM, width=1)
            for dy in [-48, -28, 32, 48]:
                dx = math.sqrt(max(0, r**2-dy**2))
                c.create_line(cx-dx, cy+dy, cx+dx, cy+dy,
                              fill=CIANO_DIM, width=1, dash=(3, 6))
            c.create_text(cx, cy-14, text="J.A.R.V.I.S", font=("Courier", 14, "bold"), fill=CIANO)
            agora = datetime.datetime.now().strftime("%H:%M:%S")
            c.create_text(cx, cy+6,  text=agora, font=("Courier", 10), fill=BRANCO)
            ia_lbl = "IA ONLINE" if API_KEY else "IA OFFLINE"
            ia_cor = ROXO if API_KEY else CINZA
            c.create_text(cx, cy+24, text=ia_lbl, font=("Courier", 9), fill=ia_cor)
            self._angle = (self._angle + 2) % 360
            self._pulse += 0.05 * self._pulse_dir
            if self._pulse >= 1 or self._pulse <= 0: self._pulse_dir *= -1
            self.root.after(40, self._animar)

        def _log(self, texto, tag="c"):
            self.log.config(state="normal")
            self.log.insert("end", texto + "\n", tag)
            self.log.see("end")
            self.log.config(state="disabled")

        def responder(self, texto, tag="c"):
            h = datetime.datetime.now().strftime("%H:%M")
            self._log(f"[{h}] 🤖 {texto}", tag)
            falar(texto)

        def _log_extra(self, texto, cor=None):
            self._log(f"  {texto}", "d")

        def _cmd(self, texto):
            threading.Thread(
                target=processar,
                args=(texto, self.responder, self._log_extra,
                      lambda msg: self.root.after(0, lambda: self._log(msg, "y"))),
                daemon=True
            ).start()

        def _enviar(self, event=None):
            cmd = self.entry.get().strip()
            if cmd:
                self._log(f"▶ {cmd}", "d")
                self.entry.delete(0, "end")
                self._cmd(cmd)

        def _dialog_lembrete(self):
            resp = simpledialog.askstring(
                "Novo Lembrete",
                "Ex: reunião em 30 minutos\nEx: às 15h ligar pro cliente\n"
                "Ex: amanhã às 9h devocional\nEx: toda segunda às 8h oração",
                parent=self.root)
            if resp: self._cmd(f"lembrete {resp}")

        def _dialog_pesquisa(self):
            termo = simpledialog.askstring("Pesquisar", "O que quer pesquisar?", parent=self.root)
            if termo: self._cmd(f"pesquisa {termo}")

        def _dialog_ideia(self):
            cat = simpledialog.askstring("Categoria", "loja / igreja / pessoal:",
                                         parent=self.root) or "pessoal"
            ideia = simpledialog.askstring("Salvar Ideia", "Qual é a ideia?", parent=self.root)
            if ideia: self._cmd(f"salva ideia {cat}: {ideia}")

        def _dialog_busca(self):
            termo = simpledialog.askstring("Buscar Ideias", "Palavra-chave:", parent=self.root)
            if termo: self._cmd(f"busca ideia {termo}")

        def _dialog_ia(self):
            perg = simpledialog.askstring("Perguntar à IA", "Sua pergunta:", parent=self.root)
            if perg:
                self._log(f"▶ {perg}", "d")
                def _ok(r):  self.root.after(0, lambda: self.responder(r, "p"))
                def _err(e): self.root.after(0, lambda: self.responder(f"⚠️ {e}", "r"))
                threading.Thread(target=perguntar_ia, args=(perg, _ok, _err), daemon=True).start()

        def _saudacao_inicial(self):
            self.responder(saudacao())
            ref, txt = versiculo_do_dia()
            self._log(f"✝️  {ref}: \"{txt}\"", "g")

    root = tk.Tk()
    JarvisApp(root)
    root.mainloop()

# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    _init_voz()
    if TEM_GUI:
        try:
            run_gui()
        except Exception as e:
            print(f"Erro na GUI: {e}. Rodando no terminal.")
            run_terminal()
    else:
        run_terminal()
