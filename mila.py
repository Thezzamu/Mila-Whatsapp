import json
import random
import time
from datetime import datetime, timedelta
from dateutil.parser import parse

# --------------------------------------------------
# UTILITIES
# --------------------------------------------------

def now_ts():
    return time.time()

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


# --------------------------------------------------
# MEMORIA SELETTIVA
# --------------------------------------------------

def remember_event(state, tipo, peso):
    """
    tipo: 'positivo' | 'negativo' | 'ambiguo'
    peso: float 0.0 - 1.0
    """
    ev = {
        "tipo": tipo,
        "peso": peso,
        "timestamp": now_ts()
    }

    memory = state.get("memoria_eventi", [])
    memory.append(ev)

    max_len = state.get("memoria_massima", 30)
    if len(memory) > max_len:
        memory.pop(0)

    state["memoria_eventi"] = memory


def decay_and_distort_memory(state):
    memory = state.get("memoria_eventi", [])
    new_mem = []
    now = now_ts()

    for ev in memory:
        age_days = (now - ev["timestamp"]) / 86400

        # decadimento naturale
        ev["peso"] *= max(0.85 ** age_days, 0.1)

        # i negativi resistono di più
        if ev["tipo"] == "negativo":
            ev["peso"] *= 1.1

        # gli ambigui spariscono facilmente
        if ev["tipo"] == "ambiguo" and ev["peso"] < 0.15:
            continue

        if ev["peso"] < 0.05:
            continue

        new_mem.append(ev)

    state["memoria_eventi"] = new_mem


def emotional_bias(state):
    bias = 0.0
    for ev in state.get("memoria_eventi", []):
        if ev["tipo"] == "negativo":
            bias -= ev["peso"]
        elif ev["tipo"] == "positivo":
            bias += ev["peso"] * 0.7
    return bias


# --------------------------------------------------
# MEMORIA EMOTIVA A LUNGO TERMINE
# --------------------------------------------------

def update_emotional_memory(state, event):
    """
    event:
    - 'attenzione'
    - 'assenza'
    - 'pressione'
    - 'coerenza'
    """
    pos = state.get("memoria_positiva", 0.0)
    neg = state.get("memoria_negativa", 0.0)

    if event == "attenzione":
        pos += 0.02
        neg -= 0.01
    elif event == "assenza":
        neg += 0.03
    elif event == "pressione":
        neg += 0.04
    elif event == "coerenza":
        pos += 0.015

    state["memoria_positiva"] = clamp(pos)
    state["memoria_negativa"] = clamp(neg)

    balance = state["memoria_negativa"] - state["memoria_positiva"]
    if balance > 0.15:
        state["risentimento"] = clamp(state.get("risentimento", 0.0) + 0.02)


# --------------------------------------------------
# EVENTI DI VITA
# --------------------------------------------------

def mila_event_tick(state):
    # probabilità bassa, effetto lungo
    if random.random() > 0.02:
        return

    event = random.choice(["esami", "stress", "viaggio", "cambiamento", None])

    if event == "esami":
        state["fase_vita"] = "esami"
        state["mood"] = "stress"
    elif event == "stress":
        state["mood"] = "no_period"
    elif event == "viaggio":
        state["fase_vita"] = "viaggio"
        state["mood"] = "neutra"
    elif event == "cambiamento":
        state["fase_vita"] = "cambiamento"
        state["mood"] = "neutra"


# --------------------------------------------------
# STILE (EVOLUTIVO)
# --------------------------------------------------

def mila_style(confidenza):
    if confidenza < 0.3:
        return "fredda"
    if confidenza < 0.6:
        return "neutra"
    return "calda"


# --------------------------------------------------
# INIZIATIVA SPONTANEA
# --------------------------------------------------

def mila_maybe_initiate(state):
    hour = datetime.now().hour

    # notte
    if 1 <= hour <= 9:
        return None

    if state.get("confidenza", 0.0) < 0.6:
        return None

    if state.get("mood") == "no_period":
        return None

    if state.get("risentimento", 0.0) > 0.3:
        return None

    silence = now_ts() - state.get("ultimo_messaggio_utente", 0)
    if silence < random.uniform(3*3600, 36*3600):
        return None

    if random.random() > 0.25:
        return None

    return random.choice([
        "ehi",
        "che fai",
        "boh mi è venuto in mente",
        "stavo pensando a una cosa",
        "ti va di parlare un attimo"
    ])


# --------------------------------------------------
# CORE: MILA REPLY v3 FINALE
# --------------------------------------------------

def mila_reply(text, state):
    decay_and_distort_memory(state)
    mila_event_tick(state)

    text_raw = text.strip()
    t = text_raw.lower()
    hour = datetime.now().hour

    # aggiornamento tempi
    state["ultimo_messaggio_utente"] = now_ts()

    conf = state.get("confidenza", 0.1)
    interesse = state.get("interesse", 0.1)
    ris = state.get("risentimento", 0.0)
    mood = state.get("mood", "neutra")
    fase = state.get("fase_vita", "standard")

    bias = emotional_bias(state)

    # mood latente
    if bias < -0.3:
        state["mood"] = "chiusa"
    elif bias > 0.4:
        state["mood"] = "aperta"

    style = mila_style(conf)

    # notte = spesso silenzio
    if 2 <= hour <= 9 and random.random() < 0.8:
        remember_event(state, "ambiguo", 0.05)
        return None

    # ritardi realistici (gestiti a monte, qui solo filtro)
    if random.random() < (0.2 + ris):
        return None

    # PERIODI NO
    if mood == "no_period":
        if random.random() < 0.6:
            remember_event(state, "negativo", 0.1)
            return None
        return random.choice(["boh", "mah", "lascia stare"])

    # SALUTI
    if any(x in t for x in ["ciao", "hey", "ehi"]):
        if style == "fredda":
            return random.choice(["ciao", "hey"])
        if style == "neutra":
            return random.choice(["ciao", "hey tu", "mmh dimmi"])
        return random.choice(["ehi", "ciao", "che fai"])

    # COME STAI
    if "come stai" in t:
        if conf < 0.4:
            return random.choice(["bene", "ok", "normale"])
        return random.choice(["stanca", "meh", "abbastanza bene"])

    # ALTRE RAGAZZE → gelosia silenziosa
    if any(x in t for x in ["un'altra", "una tipa", "una ragazza"]):
        state["gelosia"] = clamp(state.get("gelosia", 0.0) + 0.1)
        remember_event(state, "negativo", 0.2)
        return None if conf < 0.5 else random.choice(["ah", "ok", "capito"])

    # INVITI
    if any(x in t for x in ["uscire", "vederci", "palestra", "allenarci"]):
        remember_event(state, "positivo", 0.1)
        if conf < 0.3:
            return random.choice(["non so", "forse", "vediamo"])
        if conf < 0.6:
            return random.choice(["potrei", "dipende", "forse sì"])
        return random.choice(["ci sta", "mmh magari"])

    # CONFIDENZA ALTA → micro aperture
    if conf > 0.7 and random.random() < 0.3:
        return random.choice([
            "oggi sono un po strana",
            "sono stanca morta",
            "non ho dormito molto"
        ])

    # CORREZIONI
    if random.random() < 0.1:
        return random.choice(["cioè", "anzi no", "aspetta"])

    # MESSAGGIO CANCELLATO
    if random.random() < 0.07:
        return "— messaggio eliminato —"

    # FALLBACK UMANO
    fallback = ["boh", "mah", "non lo so", "dipende", "mmh"]

    if ris > 0.4:
        return random.choice(["boh", "mah"])

    return random.choice(fallback)

