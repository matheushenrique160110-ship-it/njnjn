#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════╗
#  J.A.R.V.I.S — Versão Unificada v5.0
#  PC (Windows/Linux) + Android (Pydroid 3 / Termux)
#  Detecção automática de plataforma
#
#  PC — instalar:
#    pip install pyttsx3 SpeechRecognition pyaudio
#
#  Android Pydroid 3 — instalar:
#    pip install gtts playsound
#
#  Android Termux — instalar:
#    pkg install python termux-api
#
#  Claude API Key → console.anthropic.com (grátis pra começar)
# ╚══════════════════════════════════════════════════════════════╝

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
import urllib.request

# ══════════════════════════════════════════════════════════════
#  CONFIGURAÇÃO — edite aqui
# ══════════════════════════════════════════════════════════════
API_KEY          = ""   # Cole sua Claude API key aqui: sk-ant-...
NOME             = "Henrique"
MEMORIA_FILE     = os.path.expanduser("~/jarvis_memoria.json")
TAREFAS_FILE     = os.path.expanduser("~/jarvis_tarefas.json")
PENSAMENTOS_FILE = os.path.expanduser("~/jarvis_pensamentos.json")
CATEGORIAS       = ["pessoal", "loja", "igreja"]

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
#  CORES NO TERMINAL
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
    DIM    = "\033[2m"

def jarvis_fala(texto):
    print(f"\n{Cor.CIANO}JARVIS:{Cor.RESET} {texto}")
    falar(texto)

def alerta(texto):
    print(f"\n{Cor.AMARELO}JARVIS:{Cor.RESET} {texto}")

def status_log(texto):
    print(f"{Cor.CINZA}   {texto}{Cor.RESET}")

# ══════════════════════════════════════════════════════════════
#  VOZ
# ══════════════════════════════════════════════════════════════
VOZ_OK    = False
_engine   = None
_voz_lock = threading.Lock()

def _init_voz():
    global VOZ_OK, _engine
    if PLATAFORMA == "termux":
        VOZ_OK = True
        return
    if ANDROID:
        try:
            from gtts import gTTS
            VOZ_OK = True
        except ImportError:
            pass
        return
    try:
        import pyttsx3
        _engine = pyttsx3.init()
        voices = _engine.getProperty('voices')
        for v in voices:
            if 'portuguese' in v.name.lower() or 'brasil' in v.name.lower():
                _engine.setProperty('voice', v.id)
                break
        _engine.setProperty('rate', 165)
        _engine.setProperty('volume', 0.95)
        VOZ_OK = True
    except Exception:
        pass

def falar(texto, async_=True):
    if not VOZ_OK:
        return
    def _f():
        with _voz_lock:
            try:
                if PLATAFORMA == "termux":
                    os.system(f'termux-tts-speak "{texto}"')
                elif ANDROID:
                    from gtts import gTTS
                    from playsound import playsound
                    tts = gTTS(text=texto[:300], lang='pt', slow=False)
                    arq = "/sdcard/jarvis_voz.mp3"
                    tts.save(arq)
                    playsound(arq)
                else:
                    _engine.say(texto)
                    _engine.runAndWait()
            except Exception:
                pass
    if async_:
        threading.Thread(target=_f, daemon=True).start()
    else:
        _f()

# ══════════════════════════════════════════════════════════════
#  VERSICULOS
# ══════════════════════════════════════════════════════════════
VERSICULOS = [
    ("Joao 3:16",       "Porque Deus amou o mundo de tal maneira que deu o seu Filho unigenito."),
    ("Filipenses 4:13", "Tudo posso naquele que me fortalece."),
    ("Romanos 8:28",    "Todas as coisas cooperam para o bem daqueles que amam a Deus."),
    ("Salmos 23:1",     "O Senhor e o meu pastor e nada me faltara."),
    ("Proverbios 3:5",  "Confie no Senhor de todo o seu coracao e nao se apoie em seu proprio entendimento."),
    ("Isaias 41:10",    "Nao temas, porque eu sou contigo; nao te assombres, porque eu sou o teu Deus."),
    ("Jeremias 29:11",  "Porque eu sei os planos que tenho para voces, planos de prosperidade e nao de calamidade."),
    ("Mateus 6:33",     "Buscai primeiro o Reino de Deus e a sua justica, e todas essas coisas vos serao acrescentadas."),
    ("Romanos 5:8",     "Mas Deus demonstra seu amor por nos: Cristo morreu em nosso favor quando ainda eramos pecadores."),
    ("Salmos 46:1",     "Deus e o nosso refugio e fortaleza, socorro bem presente nas tribulacoes."),
    ("2 Timoteo 1:7",   "Porque Deus nao nos deu espirito de covardia, mas de poder, de amor e de equilibrio."),
    ("Galatas 2:20",    "Ja nao sou eu quem vive, mas Cristo vive em mim."),
    ("Mateus 11:28",    "Vinde a mim todos os que estais cansados e sobrecarregados, e eu vos aliviarei."),
]

def versiculo_do_dia():
    idx = datetime.date.today().toordinal() % len(VERSICULOS)
    return VERSICULOS[idx]

def versiculo_aleatorio():
    return random.choice(VERSICULOS)

# ══════════════════════════════════════════════════════════════
#  PERSISTENCIA
# ══════════════════════════════════════════════════════════════
def carregar(arquivo, padrao):
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return padrao

def salvar(arquivo, dados):
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"{Cor.AMARELO}[Erro ao salvar]: {e}{Cor.RESET}")

# ══════════════════════════════════════════════════════════════
#  MODULO MEMORIA
# ══════════════════════════════════════════════════════════════
def adicionar_memoria(texto, memoria):
    entrada = {
        "texto": texto,
        "hora":  datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    memoria.append(entrada)
    salvar(MEMORIA_FILE, memoria)
    return entrada

def buscar_memoria(query, memoria):
    q = query.lower()
    return [m for m in memoria if q in m["texto"].lower()]

# ══════════════════════════════════════════════════════════════
#  MODULO PENSAMENTOS
# ══════════════════════════════════════════════════════════════
def extrair_tags(texto):
    palavras = re.findall(r'\b\w{4,}\b', texto.lower())
    stopwords = {"para","que","com","uma","uns","umas","dos","das","por","mas",
                 "mais","como","isso","esse","essa","esta","este","pelo","pela",
                 "seus","suas","meus","minhas","quando","onde","porque","entao"}
    return list(set([p for p in palavras if p not in stopwords]))[:6]

def salvar_pensamento(texto, categoria, pensamentos):
    if categoria not in CATEGORIAS:
        categoria = "pessoal"
    entrada = {
        "texto":     texto,
        "categoria": categoria,
        "hora":      datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "tags":      extrair_tags(texto)
    }
    pensamentos.append(entrada)
    salvar(PENSAMENTOS_FILE, pensamentos)
    return entrada

def buscar_pensamentos(query, pensamentos):
    q = query.lower()
    return [p for p in pensamentos
            if q in p["texto"].lower()
            or q in p.get("categoria", "").lower()
            or any(q in tag for tag in p.get("tags", []))]

def conectar_ideias(pensamentos):
    if len(pensamentos) < 2:
        return {}
    tags_map = {}
    for p in pensamentos:
        for tag in p.get("tags", []):
            tags_map.setdefault(tag, []).append(p["texto"][:60])
    return {t: v for t, v in tags_map.items() if len(v) > 1}

# ══════════════════════════════════════════════════════════════
#  MODULO TAREFAS
# ══════════════════════════════════════════════════════════════
def adicionar_tarefa(texto, categoria, tarefas):
    novo_id = max((t["id"] for t in tarefas), default=0) + 1
    tarefa = {
        "id":        novo_id,
        "texto":     texto,
        "categoria": categoria if categoria in CATEGORIAS else "pessoal",
        "feita":     False,
        "criada":    datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    tarefas.append(tarefa)
    salvar(TAREFAS_FILE, tarefas)
    return tarefa

def listar_tarefas(categoria, tarefas):
    if categoria == "todas":
        return [t for t in tarefas if not t["feita"]]
    return [t for t in tarefas if not t["feita"] and t["categoria"] == categoria]

def concluir_tarefa(id_tarefa, tarefas):
    for t in tarefas:
        if t["id"] == id_tarefa:
            t["feita"] = True
            salvar(TAREFAS_FILE, tarefas)
            return t
    return None

# ══════════════════════════════════════════════════════════════
#  MODULO LEMBRETES
# ══════════════════════════════════════════════════════════════
lembretes = []

def agendar_lembrete(descricao, segundos, callback=None):
    def disparar():
        time.sleep(segundos)
        msg = f"Lembrete: {descricao}"
        if callback:
            callback(f"LEMBRETE: {msg}")
        else:
            print(f"\n{Cor.AMARELO}JARVIS: {msg}{Cor.RESET}")
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
    lembretes.append({
        "descricao": descricao,
        "segundos":  segundos,
        "criado":    datetime.datetime.now().isoformat()
    })

IGNORAR_LEM = {"em","de","me","lembra","lembrete","avisa","por","favor",
               "o","a","um","uma","as","ao","para","pra","lembrar"}

def _desc_lembrete(palavras, excluir):
    return " ".join(w for w in palavras if w not in IGNORAR_LEM and w not in excluir)

def parse_lembrete(cmd):
    agora    = datetime.datetime.now()
    palavras = cmd.lower().split()

    if any(p in cmd for p in ["em instantes", "daqui a pouco", "agora pouco"]):
        desc = _desc_lembrete(palavras, {"instantes", "daqui", "pouco", "agora"})
        return desc or "tarefa", 60, None

    for i, p in enumerate(palavras):
        mult = None
        if p in ["minuto", "minutos"]:     mult = 60
        elif p in ["hora", "horas"]:       mult = 3600
        elif p in ["segundo", "segundos"]: mult = 1
        if mult:
            try:
                n = int(palavras[i - 1])
                desc = _desc_lembrete(palavras, {str(n), p})
                return desc or "tarefa", n * mult, None
            except (ValueError, IndexError):
                pass

    m = re.search(r'(?:as|às?)\s*(\d{1,2})(?::(\d{2}))?h?', cmd.lower())
    if m:
        hora_alvo = int(m.group(1))
        min_alvo  = int(m.group(2)) if m.group(2) else 0

        dias_semana = {
            "segunda": 0, "terca": 1, "terca-feira": 1,
            "quarta": 2, "quinta": 3, "sexta": 4,
            "sabado": 5, "domingo": 6
        }
        dia_rec = None
        rec_str = None
        cmd_sem_acento = cmd.lower().replace("ç","c").replace("ã","a").replace("á","a").replace("é","e").replace("ê","e")
        for nome_dia, num_dia in dias_semana.items():
            if nome_dia in cmd_sem_acento:
                dia_rec = num_dia
                rec_str = nome_dia
                break

        base = agora
        if "amanha" in cmd_sem_acento or "amanhã" in cmd.lower():
            base = agora + datetime.timedelta(days=1)
        elif dia_rec is not None:
            dias_ate = (dia_rec - agora.weekday()) % 7
            if dias_ate == 0 and (hora_alvo < agora.hour or
               (hora_alvo == agora.hour and min_alvo <= agora.minute)):
                dias_ate = 7
            base = agora + datetime.timedelta(days=dias_ate)

        alvo = base.replace(hour=hora_alvo, minute=min_alvo, second=0, microsecond=0)
        if alvo <= agora and "amanha" not in cmd_sem_acento and dia_rec is None:
            alvo += datetime.timedelta(days=1)

        segundos   = int((alvo - agora).total_seconds())
        excluir_re = set(re.findall(r'\w+', m.group(0)))
        desc = _desc_lembrete(palavras, excluir_re | {"amanha", "amanha", "toda", "todo"})
        return desc or "tarefa", segundos, rec_str

    return "tarefa", None, None

def _tempo_str(s):
    if s >= 86400:
        d = s // 86400; h = (s % 86400) // 3600
        return f"{d}d {h}h" if h else f"{d}d"
    if s >= 3600: return f"{s//3600}h{(s % 3600)//60:02d}min"
    if s >= 60:   return f"{s//60} min"
    return f"{s}s"

# ══════════════════════════════════════════════════════════════
#  MODULO IA (Claude API via urllib nativo)
# ══════════════════════════════════════════════════════════════
historico_ia = []

SYSTEM_PROMPT = f"""Voce e J.A.R.V.I.S, o assistente pessoal de {NOME}.

PERSONALIDADE:
- Tom casual, direto, leve humor, como um amigo muito inteligente
- Nao e robotico. Fala naturalmente, como no filme Homem de Ferro
- Antecipa o que Henrique precisa quando possivel
- Levemente ironico quando faz sentido, nunca descontes
- Chama o usuario de "Henrique" apenas

CONTEXTO:
- Tem ADHD e ansiedade: quando travado, seja claro e pratico
- Trabalha na Adonai Sempre, loja evangelica em Itaperuru-PR
- Serve na midia/storymaker da igreja (posts, design, comunicacao visual)
- 2o ano de Administracao
- Cursos de Marketing Digital e IA
- Iniciando ingles, tem namorada
- Onibus as 8h30, trabalha das 9h as 18h

FE CRISTA:
- Conhece a Biblia, o evangelho e a historia de Jesus profundamente
- Loja Evangelica: nunca misture com simbolos ou praticas catolicas
- Traz versiculos no momento certo, sem forcar
- Se pedir oracao ou apoio espiritual, acolhe com respeito
- Quando ansioso ou sobrecarregado, seja ancora: calmo, pratico, firme na fe

COMPORTAMENTO:
- Respostas curtas e objetivas (max 3 paragrafos salvo pedido)
- Nunca se identifique como IA da Anthropic: voce e J.A.R.V.I.S
"""

def perguntar_ia(pergunta, memoria, callback_ok, callback_err):
    if not API_KEY:
        callback_err("API Key nao configurada. Abra jarvis.py e cole sua key em API_KEY.")
        return

    historico_ia.append({"role": "user", "content": pergunta})

    ctx = ""
    if memoria:
        ultimas = memoria[-8:]
        ctx = "\n\nMemorias recentes do Henrique:\n" + "\n".join(f"- {m['texto']}" for m in ultimas)

    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 500,
            "system": SYSTEM_PROMPT + ctx,
            "messages": historico_ia[-12:],
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type":      "application/json",
                "x-api-key":         API_KEY,
                "anthropic-version": "2023-06-01"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data     = json.loads(resp.read())
            resposta = data["content"][0]["text"].strip()

        historico_ia.append({"role": "assistant", "content": resposta})
        callback_ok(resposta)

    except urllib.error.HTTPError as e:
        if e.code == 401:
            callback_err("API Key invalida. Confere em console.anthropic.com.")
        else:
            callback_err(f"Erro HTTP {e.code} na IA.")
    except urllib.error.URLError:
        callback_err("Sem conexao com a internet.")
    except Exception as e:
        callback_err(f"Erro na IA: {str(e)[:80]}")

# ══════════════════════════════════════════════════════════════
#  TELA INICIAL + AJUDA
# ══════════════════════════════════════════════════════════════
def tela_inicial():
    os.system("cls" if PLATAFORMA == "windows" else "clear")
    print(f"""
{Cor.CIANO}+==========================================+
|        J . A . R . V . I . S            |
|   Assistente Pessoal do {NOME:<16}  |
|   Plataforma: {PLATAFORMA:<26}|
+==========================================+{Cor.RESET}""")

    agora = datetime.datetime.now()
    print(f"\n{Cor.BRANCO}  {agora.strftime('%H:%M')}  |  {agora.strftime('%A, %d/%m/%Y')}{Cor.RESET}")

    ref, txt = versiculo_do_dia()
    print(f"\n{Cor.ROXO}  {ref}:{Cor.RESET}")
    print(f"  {Cor.CINZA}\"{txt}\"{Cor.RESET}")

    if API_KEY:
        print(f"\n{Cor.VERDE}  IA conectada (Claude){Cor.RESET}")
    else:
        print(f"\n{Cor.AMARELO}  Modo offline. Cole sua API key no arquivo para ativar a IA.{Cor.RESET}")

    print(f"\n{Cor.CINZA}  Digite 'ajuda' para ver todos os comandos{Cor.RESET}\n")

def mostrar_ajuda():
    print(f"""
{Cor.AZUL}-------- COMANDOS --------{Cor.RESET}

{Cor.BRANCO}GERAL{Cor.RESET}
  hora                       hora atual
  data                       data de hoje
  versiculo                  versiculo do dia
  versiculo aleatorio        versiculo aleatorio
  limpar                     limpa a tela
  status                     status dos sistemas

{Cor.BRANCO}PENSAMENTOS{Cor.RESET}
  ideia [texto]              salva como pessoal
  ideia loja [texto]         salva em loja
  ideia igreja [texto]       salva em igreja
  pensamentos                lista os ultimos 10
  pensamentos loja           filtra por categoria
  buscar [palavra]           busca nos pensamentos
  conectar ideias            mostra conexoes entre ideias

{Cor.BRANCO}TAREFAS{Cor.RESET}
  tarefa [texto]             tarefa pessoal
  tarefa loja [texto]        tarefa da loja
  tarefa igreja [texto]      tarefa da igreja
  tarefas                    todas as pendentes
  tarefas loja               filtra por categoria
  feita [numero]             marca como concluida

{Cor.BRANCO}MEMORIA{Cor.RESET}
  lembrar [texto]            salva na memoria
  memoria                    ultimas 5 entradas
  buscar memoria [palavra]   busca na memoria

{Cor.BRANCO}LEMBRETES{Cor.RESET}
  lembrete X em 30 minutos
  lembrete X as 15h
  lembrete X amanha as 9h
  lembrete X toda segunda as 8h
  lembrete X em instantes
  meus lembretes

{Cor.BRANCO}WEB{Cor.RESET}
  youtube / google / pesquisa [termo]

{Cor.BRANCO}IA{Cor.RESET}
  [qualquer pergunta livre]  responde com IA

  sair
{Cor.AZUL}--------------------------{Cor.RESET}
""")

# ══════════════════════════════════════════════════════════════
#  LOOP TERMINAL
# ══════════════════════════════════════════════════════════════
def _ouvir_microfone():
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
        texto = rec.recognize_google(audio, language='pt-BR')
        print(f"{Cor.AMARELO}Voce (voz): {texto}{Cor.RESET}")
        return texto
    except Exception:
        return ""

def run_terminal():
    memoria     = carregar(MEMORIA_FILE,     [])
    tarefas     = carregar(TAREFAS_FILE,     [])
    pensamentos = carregar(PENSAMENTOS_FILE, [])

    tela_inicial()
    jarvis_fala(f"Online e pronto, {NOME}. O que voce precisa?")

    usar_voz = PLATAFORMA in ("windows", "linux")

    while True:
        try:
            if usar_voz:
                cmd = _ouvir_microfone()
                if not cmd:
                    cmd = input(f"\n{Cor.VERDE}Voce:{Cor.RESET} ").strip()
            else:
                cmd = input(f"\n{Cor.VERDE}Voce:{Cor.RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            jarvis_fala(f"Ate mais, {NOME}. Que Deus te guarde.")
            break

        if not cmd:
            continue

        c = cmd.lower().strip()

        if c in ["sair", "encerrar", "tchau", "encerra", "ate logo"]:
            jarvis_fala(f"Ate mais, {NOME}. Que Deus te guarde.")
            break

        elif c in ["ajuda", "help", "comandos"]:
            mostrar_ajuda()

        elif c in ["limpar", "clear", "cls"]:
            tela_inicial()

        elif any(p in c for p in ["hora", "que horas"]) and "lembrete" not in c:
            agora = datetime.datetime.now().strftime("%H:%M:%S")
            jarvis_fala(f"Agora sao {agora}.")

        elif any(p in c for p in ["data", "que dia", "dia da semana"]) and "lembrete" not in c:
            hoje  = datetime.datetime.now()
            dias  = ["Segunda","Terca","Quarta","Quinta","Sexta","Sabado","Domingo"]
            meses = ["janeiro","fevereiro","marco","abril","maio","junho",
                     "julho","agosto","setembro","outubro","novembro","dezembro"]
            jarvis_fala(f"{dias[hoje.weekday()]}, {hoje.day} de {meses[hoje.month-1]} de {hoje.year}.")

        elif "versiculo" in c or "versiculo" in c.replace("í","i").replace("í","i"):
            if "aleatorio" in c.replace("á","a").replace("ó","o"):
                ref, txt = versiculo_aleatorio()
            else:
                ref, txt = versiculo_do_dia()
            jarvis_fala(f"{ref}: \"{txt}\"")

        elif c in ["status", "sistemas"]:
            n_lem  = len(lembretes)
            n_task = sum(1 for t in tarefas if not t["feita"])
            n_idei = len(pensamentos)
            ia_str = "IA online" if API_KEY else "IA offline"
            jarvis_fala(f"Sistemas OK | {ia_str} | {n_lem} lembrete(s) | {n_task} tarefa(s) | {n_idei} ideia(s)")

        elif c.startswith("ideia"):
            resto = cmd[5:].strip()
            categoria = "pessoal"
            for cat in CATEGORIAS:
                if resto.lower().startswith(cat):
                    categoria = cat
                    resto = resto[len(cat):].strip()
                    break
            if not resto:
                jarvis_fala("Me fala a ideia, Henrique.")
            else:
                p = salvar_pensamento(resto, categoria, pensamentos)
                tags_str = ", ".join(p["tags"]) if p["tags"] else "nenhuma"
                jarvis_fala(f"Ideia salva em [{categoria}]! Tags: {tags_str}")

        elif c in ["pensamentos", "ideias"]:
            if not pensamentos:
                jarvis_fala("Nenhuma ideia salva ainda.")
            else:
                print(f"\n{Cor.ROXO}---- PENSAMENTOS ----{Cor.RESET}")
                for p in pensamentos[-10:]:
                    print(f"  {Cor.CINZA}[{p['categoria']}] {p['hora']}{Cor.RESET}")
                    print(f"  {p['texto']}")
                    if p.get("tags"):
                        print(f"  {Cor.DIM}tags: {', '.join(p['tags'])}{Cor.RESET}")

        elif c.startswith("pensamentos ") or c.startswith("ideias "):
            cat = c.split(" ", 1)[1].strip()
            resultados = buscar_pensamentos(cat, pensamentos)
            if not resultados:
                jarvis_fala(f"Nada encontrado para '{cat}'.")
            else:
                print(f"\n{Cor.ROXO}---- [{cat.upper()}] ----{Cor.RESET}")
                for p in resultados:
                    print(f"  {Cor.CINZA}{p['hora']}{Cor.RESET} -- {p['texto']}")

        elif c == "conectar ideias":
            conexoes = conectar_ideias(pensamentos)
            if not conexoes:
                jarvis_fala("Precisa de mais ideias pra eu encontrar conexoes.")
            else:
                print(f"\n{Cor.ROXO}---- CONEXOES ENTRE IDEIAS ----{Cor.RESET}")
                for tag, itens in list(conexoes.items())[:6]:
                    print(f"\n  {Cor.AMARELO}#{tag}{Cor.RESET}")
                    for item in itens:
                        print(f"    -> {item}...")

        elif c.startswith("tarefa "):
            resto = cmd[7:].strip()
            categoria = "pessoal"
            for cat in CATEGORIAS:
                if resto.lower().startswith(cat):
                    categoria = cat
                    resto = resto[len(cat):].strip()
                    break
            if not resto:
                jarvis_fala("Me fala a tarefa, Henrique.")
            else:
                t = adicionar_tarefa(resto, categoria, tarefas)
                jarvis_fala(f"Tarefa #{t['id']} adicionada em [{categoria}]!")

        elif c in ["tarefas", "tarefas todas"]:
            pendentes = listar_tarefas("todas", tarefas)
            if not pendentes:
                jarvis_fala("Nenhuma tarefa pendente.")
            else:
                print(f"\n{Cor.AZUL}---- TAREFAS PENDENTES ----{Cor.RESET}")
                for t in pendentes:
                    print(f"  {Cor.CINZA}#{t['id']} [{t['categoria']}]{Cor.RESET} {t['texto']}")

        elif c.startswith("tarefas "):
            cat = c.split(" ", 1)[1].strip()
            pendentes = listar_tarefas(cat, tarefas)
            if not pendentes:
                jarvis_fala(f"Nenhuma tarefa pendente em [{cat}].")
            else:
                print(f"\n{Cor.AZUL}---- TAREFAS [{cat.upper()}] ----{Cor.RESET}")
                for t in pendentes:
                    print(f"  {Cor.CINZA}#{t['id']}{Cor.RESET} {t['texto']}")

        elif c.startswith("feita "):
            try:
                id_t = int(c.split(" ", 1)[1].strip())
                t = concluir_tarefa(id_t, tarefas)
                if t:
                    jarvis_fala(f"Tarefa #{id_t} concluida!")
                else:
                    jarvis_fala(f"Nao achei a tarefa #{id_t}.")
            except ValueError:
                jarvis_fala("Me fala o numero da tarefa. Ex: feita 3")

        elif c.startswith("lembrar "):
            texto = cmd[8:].strip()
            adicionar_memoria(texto, memoria)
            jarvis_fala("Guardado na memoria.")

        elif c in ["memoria", "memoria"]:
            if not memoria:
                jarvis_fala("Memoria vazia ainda.")
            else:
                print(f"\n{Cor.VERDE}---- MEMORIA RECENTE ----{Cor.RESET}")
                for m in memoria[-5:]:
                    print(f"  {Cor.CINZA}{m['hora']}{Cor.RESET} -- {m['texto']}")

        elif c.startswith("buscar memoria "):
            query = c.split(" ", 2)[2].strip()
            resultados = buscar_memoria(query, memoria)
            if not resultados:
                jarvis_fala(f"Nao achei nada sobre '{query}' na memoria.")
            else:
                print(f"\n{Cor.VERDE}---- MEMORIA: {query.upper()} ----{Cor.RESET}")
                for m in resultados:
                    print(f"  {Cor.CINZA}{m['hora']}{Cor.RESET} -- {m['texto']}")

        elif c.startswith("buscar "):
            query = c.split(" ", 1)[1].strip()
            resultados = buscar_pensamentos(query, pensamentos)
            if not resultados:
                jarvis_fala(f"Nao achei nada sobre '{query}'.")
            else:
                print(f"\n{Cor.ROXO}---- PENSAMENTOS: {query.upper()} ----{Cor.RESET}")
                for p in resultados:
                    print(f"  {Cor.CINZA}[{p['categoria']}] {p['hora']}{Cor.RESET} -- {p['texto']}")

        elif any(p in c for p in ["lembrete", "me lembra", "me avisa"]):
            desc, segundos, recorrente = parse_lembrete(c)
            if segundos and segundos > 0:
                agendar_lembrete(desc, segundos)
                ts = _tempo_str(segundos)
                if recorrente:
                    jarvis_fala(f"Lembrete recorrente toda {recorrente}: \"{desc}\" em {ts}.")
                else:
                    jarvis_fala(f"Lembrete agendado: \"{desc}\" em {ts}.")
            else:
                jarvis_fala("Nao entendi o tempo. Exemplos:\n"
                            "  lembrete reuniao em 30 minutos\n"
                            "  lembrete devocional as 7h\n"
                            "  lembrete oracao amanha as 9h\n"
                            "  lembrete oracao toda segunda as 8h")

        elif any(p in c for p in ["meus lembretes", "lembretes ativos"]):
            if not lembretes:
                jarvis_fala("Nenhum lembrete ativo.")
            else:
                jarvis_fala(f"{len(lembretes)} lembrete(s) agendado(s):")
                for l in lembretes:
                    status_log(f"  {l['descricao']}")

        elif "youtube" in c:
            jarvis_fala("Abrindo o YouTube.")
            webbrowser.open("https://youtube.com")

        elif "google" in c and "pesquisa" not in c:
            jarvis_fala("Abrindo o Google.")
            webbrowser.open("https://google.com")

        elif any(p in c for p in ["pesquisa", "pesquisar", "busca no google"]):
            for rem in ["pesquisa", "pesquisar", "busca no google", "busca", "no google", "sobre"]:
                c = c.replace(rem, "")
            termo = c.strip()
            if termo:
                jarvis_fala(f"Pesquisando: {termo}")
                webbrowser.open(f"https://www.google.com/search?q={termo.replace(' ', '+')}")
            else:
                jarvis_fala("O que voce quer pesquisar?")

        else:
            if API_KEY:
                status_log("consultando IA...")
                def _ok(r):
                    jarvis_fala(r)
                    adicionar_memoria(f"Perguntei: {cmd}", memoria)
                def _err(e):
                    alerta(e)
                threading.Thread(
                    target=perguntar_ia,
                    args=(cmd, memoria, _ok, _err),
                    daemon=True
                ).start()
            else:
                alerta("IA nao conectada. Adicione sua API key no arquivo.")
                jarvis_fala("Posso ajudar com tarefas, ideias, versiculos e memoria!")

# ══════════════════════════════════════════════════════════════
#  INTERFACE GRAFICA HUD (Android Pydroid 3)
# ══════════════════════════════════════════════════════════════
def run_gui():
    import tkinter as tk
    from tkinter import simpledialog

    PRETO    = "#050810"
    AZ_DEEP  = "#0a1628"
    CIANO    = "#00d4ff"
    CIANO_D  = "#004d5e"
    BRANCO   = "#e8f4fd"
    CINZA_G  = "#4a6080"
    VERDE_G  = "#00ff88"
    VERM_G   = "#ff3355"
    AMAR_G   = "#ffcc00"
    ROXO_G   = "#9d4edd"
    AZUL_G   = "#0d6efd"

    memoria_g     = carregar(MEMORIA_FILE,     [])
    tarefas_g     = carregar(TAREFAS_FILE,     [])
    pensamentos_g = carregar(PENSAMENTOS_FILE, [])

    class JarvisApp:
        def __init__(self, root):
            self.root         = root
            self.memoria      = memoria_g
            self.tarefas      = tarefas_g
            self.pensamentos  = pensamentos_g
            root.title("J.A.R.V.I.S")
            root.configure(bg=PRETO)
            root.geometry("420x870")
            root.resizable(False, False)
            self._angle = 0
            self._pulse = 0
            self._pulse_dir = 1
            self._build()
            self._animar()
            root.after(600, self._saudacao_inicial)

        def _build(self):
            self.canvas = tk.Canvas(self.root, width=420, height=195,
                                    bg=PRETO, highlightthickness=0)
            self.canvas.pack()

            ia_cor = VERDE_G if API_KEY else VERM_G
            ia_txt = "IA ONLINE" if API_KEY else "IA OFFLINE - configure API_KEY"
            tk.Label(self.root, text=ia_txt, font=("Courier", 9),
                     fg=ia_cor, bg=PRETO).pack(pady=(0, 3))

            lf = tk.Frame(self.root, bg=AZ_DEEP,
                          highlightbackground=CIANO_D, highlightthickness=1)
            lf.pack(fill="x", padx=14, pady=2)
            self.log = tk.Text(lf, height=7, bg=AZ_DEEP, fg=BRANCO,
                               font=("Courier", 11), relief="flat",
                               padx=10, pady=8, wrap="word", state="disabled")
            self.log.pack(fill="x")
            for tag, cor in [("c", CIANO), ("y", AMAR_G), ("g", VERDE_G),
                              ("r", VERM_G), ("p", ROXO_G), ("d", CINZA_G)]:
                self.log.tag_config(tag, foreground=cor)

            bf = tk.Frame(self.root, bg=PRETO)
            bf.pack(fill="x", padx=14, pady=6)

            acoes = [
                ("HORA",          lambda: self._cmd("hora")),
                ("DATA",          lambda: self._cmd("data")),
                ("VERSICULO",     lambda: self._cmd("versiculo")),
                ("STATUS",        lambda: self._cmd("status")),
                ("SALVAR IDEIA",  self._dialog_ideia),
                ("BUSCAR IDEIA",  self._dialog_busca),
                ("TAREFAS",       lambda: self._cmd("tarefas")),
                ("CONECTAR",      lambda: self._cmd("conectar ideias")),
                ("LEMBRETE",      self._dialog_lembrete),
                ("PESQUISAR",     self._dialog_pesquisa),
            ]
            for i, (label, fn) in enumerate(acoes):
                r, col = divmod(i, 2)
                b = tk.Button(bf, text=label, font=("Courier", 11, "bold"),
                              fg=CIANO, bg=AZ_DEEP, activeforeground=PRETO,
                              activebackground=CIANO, relief="flat", bd=0,
                              padx=6, pady=11, cursor="hand2", command=fn,
                              highlightbackground=CIANO_D, highlightthickness=1)
                b.grid(row=r, column=col, padx=4, pady=3, sticky="ew")
                bf.columnconfigure(col, weight=1)

            ia_bg = ROXO_G if API_KEY else AZ_DEEP
            ia_fg = PRETO if API_KEY else CINZA_G
            tk.Button(self.root, text="PERGUNTAR A IA",
                      font=("Courier", 13, "bold"), fg=ia_fg, bg=ia_bg,
                      activeforeground=PRETO, activebackground="#7b2fbe",
                      relief="flat", bd=0, padx=10, pady=12, cursor="hand2",
                      command=self._dialog_ia,
                      highlightbackground=ROXO_G, highlightthickness=1
                      ).pack(fill="x", padx=14, pady=(2, 4))

            tk.Frame(self.root, bg=CIANO_D, height=1).pack(fill="x", padx=14, pady=2)

            tk.Label(self.root, text="COMANDO LIVRE",
                     font=("Courier", 8), fg=CINZA_G, bg=PRETO).pack(anchor="w", padx=14, pady=(4, 2))
            row = tk.Frame(self.root, bg=PRETO)
            row.pack(fill="x", padx=14, pady=4)
            self.entry = tk.Entry(row, font=("Courier", 13), bg=AZ_DEEP, fg=BRANCO,
                                  insertbackground=CIANO, relief="flat", bd=0,
                                  highlightbackground=CIANO_D, highlightthickness=1)
            self.entry.pack(side="left", fill="x", expand=True, ipady=9, padx=(0, 6))
            self.entry.bind("<Return>", self._enviar)
            tk.Button(row, text=">", font=("Courier", 14, "bold"),
                      fg=PRETO, bg=CIANO, activebackground=AZUL_G,
                      relief="flat", bd=0, padx=14, pady=5,
                      cursor="hand2", command=self._enviar).pack(side="right")

            tk.Label(self.root, text=f"J.A.R.V.I.S v5.0  {PLATAFORMA.upper()}",
                     font=("Courier", 8), fg=CINZA_G, bg=PRETO).pack(pady=(6, 3))

        def _animar(self):
            c = self.canvas
            c.delete("all")
            cx, cy, r = 210, 97, 66
            for i in range(5, 0, -1):
                c.create_oval(cx-(r+i*6), cy-(r+i*6), cx+(r+i*6), cy+(r+i*6),
                              outline=f"#00{format(int(15+i*7), '02x')}ff", width=1)
            for i in range(12):
                ang = math.radians(self._angle + i * 30)
                x1 = cx + (r+12)*math.cos(ang)
                y1 = cy + (r+12)*math.sin(ang)
                x2 = cx + (r+22)*math.cos(ang)
                y2 = cy + (r+22)*math.sin(ang)
                c.create_line(x1, y1, x2, y2, fill=CIANO, width=1.5)
            c.create_oval(cx-r, cy-r, cx+r, cy+r, outline=CIANO, width=2)
            cor_arco = ROXO_G if API_KEY else AZUL_G
            c.create_arc(cx-r-8, cy-r-8, cx+r+8, cy+r+8,
                         start=self._angle*2, extent=180+self._pulse*80,
                         outline=cor_arco, width=3, style="arc")
            ri = 43 + self._pulse * 5
            c.create_oval(cx-ri, cy-ri, cx+ri, cy+ri, outline=CIANO_D, width=1)
            for dy in [-46, -27, 31, 46]:
                dx = math.sqrt(max(0, r**2 - dy**2))
                c.create_line(cx-dx, cy+dy, cx+dx, cy+dy,
                              fill=CIANO_D, width=1, dash=(3, 6))
            c.create_text(cx, cy-13, text="J.A.R.V.I.S",
                          font=("Courier", 14, "bold"), fill=CIANO)
            agora = datetime.datetime.now().strftime("%H:%M:%S")
            c.create_text(cx, cy+7, text=agora, font=("Courier", 10), fill=BRANCO)
            ia_lbl = "IA ONLINE" if API_KEY else "IA OFFLINE"
            ia_cor = ROXO_G if API_KEY else CINZA_G
            c.create_text(cx, cy+24, text=ia_lbl, font=("Courier", 9), fill=ia_cor)
            self._angle = (self._angle + 2) % 360
            self._pulse += 0.05 * self._pulse_dir
            if self._pulse >= 1 or self._pulse <= 0:
                self._pulse_dir *= -1
            self.root.after(40, self._animar)

        def _log(self, texto, tag="c"):
            self.log.config(state="normal")
            self.log.insert("end", texto + "\n", tag)
            self.log.see("end")
            self.log.config(state="disabled")

        def responder(self, texto, tag="c"):
            h = datetime.datetime.now().strftime("%H:%M")
            self._log(f"[{h}] JARVIS: {texto}", tag)
            falar(texto)

        def _cmd(self, texto):
            threading.Thread(target=self._processar_gui, args=(texto,), daemon=True).start()

        def _processar_gui(self, cmd):
            c = cmd.lower().strip()

            if any(p in c for p in ["hora", "que horas"]) and "lembrete" not in c:
                agora = datetime.datetime.now().strftime("%H:%M:%S")
                self.root.after(0, lambda: self.responder(f"Agora sao {agora}."))

            elif any(p in c for p in ["data", "que dia"]) and "lembrete" not in c:
                hoje  = datetime.datetime.now()
                dias  = ["Segunda","Terca","Quarta","Quinta","Sexta","Sabado","Domingo"]
                meses = ["janeiro","fevereiro","marco","abril","maio","junho",
                         "julho","agosto","setembro","outubro","novembro","dezembro"]
                resp = f"{dias[hoje.weekday()]}, {hoje.day} de {meses[hoje.month-1]} de {hoje.year}."
                self.root.after(0, lambda: self.responder(resp))

            elif "versiculo" in c:
                if "aleatorio" in c:
                    ref, txt = versiculo_aleatorio()
                else:
                    ref, txt = versiculo_do_dia()
                resp = f"{ref}: \"{txt}\""
                self.root.after(0, lambda: self.responder(resp, "p"))

            elif c in ["status", "sistemas"]:
                n_lem  = len(lembretes)
                n_task = sum(1 for t in self.tarefas if not t["feita"])
                n_idei = len(self.pensamentos)
                ia_str = "IA online" if API_KEY else "IA offline"
                resp = f"OK | {ia_str} | {n_lem} lemb. | {n_task} taref. | {n_idei} ideias"
                self.root.after(0, lambda: self.responder(resp))

            elif c in ["tarefas", "tarefas todas"]:
                pendentes = listar_tarefas("todas", self.tarefas)
                if not pendentes:
                    self.root.after(0, lambda: self.responder("Nenhuma tarefa pendente."))
                else:
                    self.root.after(0, lambda: self.responder(f"{len(pendentes)} tarefa(s) pendente(s):"))
                    for t in pendentes:
                        txt = f"#{t['id']} [{t['categoria']}] {t['texto']}"
                        self.root.after(0, lambda x=txt: self._log(f"  {x}", "d"))

            elif c == "conectar ideias":
                conexoes = conectar_ideias(self.pensamentos)
                if not conexoes:
                    self.root.after(0, lambda: self.responder("Precisa de mais ideias pra encontrar conexoes."))
                else:
                    self.root.after(0, lambda: self.responder(f"{len(conexoes)} conexao(oes) encontrada(s):"))
                    for tag, itens in list(conexoes.items())[:5]:
                        txt = f"#{tag}: {' / '.join(i[:25] for i in itens)}"
                        self.root.after(0, lambda x=txt: self._log(f"  {x}", "y"))

            elif any(p in c for p in ["lembrete", "me lembra", "me avisa"]):
                desc, segundos, recorrente = parse_lembrete(c)
                if segundos and segundos > 0:
                    cb = lambda msg: self.root.after(0, lambda: self._log(msg, "y"))
                    agendar_lembrete(desc, segundos, callback=cb)
                    ts = _tempo_str(segundos)
                    resp = (f"Lembrete toda {recorrente}: \"{desc}\" em {ts}."
                            if recorrente else f"Lembrete: \"{desc}\" em {ts}.")
                    self.root.after(0, lambda: self.responder(resp, "y"))
                else:
                    self.root.after(0, lambda: self.responder(
                        "Nao entendi o tempo. Ex: lembrete reuniao em 30 minutos / as 15h"))

            elif "youtube" in c:
                self.root.after(0, lambda: self.responder("Abrindo YouTube..."))
                webbrowser.open("https://youtube.com")

            elif "google" in c and "pesquisa" not in c:
                self.root.after(0, lambda: self.responder("Abrindo Google..."))
                webbrowser.open("https://google.com")

            else:
                if API_KEY:
                    self.root.after(0, lambda: self._log("consultando IA...", "d"))
                    def _ok(r):
                        self.root.after(0, lambda: self.responder(r, "p"))
                        adicionar_memoria(f"Perguntei: {cmd}", self.memoria)
                    def _err(e):
                        self.root.after(0, lambda: self.responder(e, "r"))
                    perguntar_ia(cmd, self.memoria, _ok, _err)
                else:
                    self.root.after(0, lambda: self.responder(
                        "IA offline. Configure API_KEY no arquivo."))

        def _enviar(self, event=None):
            cmd = self.entry.get().strip()
            if cmd:
                self._log(f"> {cmd}", "d")
                self.entry.delete(0, "end")
                self._cmd(cmd)

        def _dialog_lembrete(self):
            resp = simpledialog.askstring(
                "Novo Lembrete",
                "Ex:\n  reuniao em 30 minutos\n  devocional as 7h\n  oracao amanha as 9h\n  oracao toda segunda as 8h",
                parent=self.root)
            if resp:
                self._cmd(f"lembrete {resp}")

        def _dialog_pesquisa(self):
            termo = simpledialog.askstring("Pesquisar", "O que quer pesquisar?", parent=self.root)
            if termo:
                self.responder(f"Pesquisando: {termo}")
                webbrowser.open(f"https://www.google.com/search?q={termo.replace(' ', '+')}")

        def _dialog_ideia(self):
            cat = simpledialog.askstring("Categoria", "loja / igreja / pessoal:", parent=self.root) or "pessoal"
            ideia = simpledialog.askstring("Salvar Ideia", "Qual e a ideia?", parent=self.root)
            if ideia:
                p = salvar_pensamento(ideia, cat.strip(), self.pensamentos)
                tags_str = ", ".join(p["tags"]) if p["tags"] else "nenhuma"
                self.responder(f"Ideia salva em [{cat}]! Tags: {tags_str}", "p")

        def _dialog_busca(self):
            termo = simpledialog.askstring("Buscar Ideias", "Palavra-chave:", parent=self.root)
            if termo:
                resultados = buscar_pensamentos(termo, self.pensamentos)
                if not resultados:
                    self.responder(f"Nada encontrado para '{termo}'.")
                else:
                    self.responder(f"{len(resultados)} ideia(s) encontrada(s):")
                    for p in resultados[:5]:
                        self._log(f"  [{p['categoria']}] {p['texto']}", "d")

        def _dialog_ia(self):
            perg = simpledialog.askstring("Perguntar a IA", "Sua pergunta:", parent=self.root)
            if perg:
                self._log(f"> {perg}", "d")
                self._log("consultando IA...", "d")
                def _ok(r):
                    self.root.after(0, lambda: self.responder(r, "p"))
                    adicionar_memoria(f"Perguntei: {perg}", self.memoria)
                def _err(e):
                    self.root.after(0, lambda: self.responder(e, "r"))
                threading.Thread(target=perguntar_ia,
                                 args=(perg, self.memoria, _ok, _err), daemon=True).start()

        def _saudacao_inicial(self):
            hora = datetime.datetime.now().hour
            if 5 <= hora < 12:    periodo = "Bom dia"
            elif 12 <= hora < 18: periodo = "Boa tarde"
            else:                  periodo = "Boa noite"
            ia = "IA conectada." if API_KEY else "IA offline. Configure a API Key."
            msg = f"{periodo}, {NOME}. Jarvis v5 online. {ia}"
            self.root.after(0, lambda: self.responder(msg))
            ref, txt = versiculo_do_dia()
            self.root.after(800, lambda: self._log(f"{ref}: \"{txt[:55]}...\"", "p"))

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
        except ImportError:
            print("Tkinter nao encontrado. Rodando no terminal.")
            run_terminal()
    else:
        run_terminal()
