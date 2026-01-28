import json
import random
from datetime import datetime, timedelta
from dateutil.parser import parse

MEMORY_FILE = "memory.json"

def load_memory():
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(mem):
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=2)

def fascia_oraria():
    h = datetime.now().hour
    if 6 <= h < 10: return "mattina"
    if 10 <= h < 18: return "giorno"
    if 18 <= h < 23: return "sera"
    return "notte"

def should_respond(mem):
    fascia = fascia_oraria()
    base = 0.35 + mem["confidenza"]

    if fascia == "notte":
        base -= 0.5
    if mem["stile"] == "freddo":
        base -= 0.15
    if mem["giorni_silenzio"] > 2:
        base += 0.25

    return random.random() < max(0.05, min(base, 0.95))

def update_confidenza(mem, text):
    if len(text) > 40:
        mem["confidenza"] += 0.02
    if "ti penso" in text:
        mem["confidenza"] += 0.04
    mem["confidenza"] = min(mem["confidenza"], 0.9)

def evolve_stile(mem):
    if mem["confidenza"] > 0.6:
        mem["stile"] = "caldo"
    elif mem["confidenza"] > 0.3:
        mem["stile"] = "neutro"

def mila_reply(user_text):
    mem = load_memory()
    now = datetime.now()

    if mem["ultima_interazione"]:
        last = parse(mem["ultima_interazione"])
        if (now - last).days >= 1:
            mem["giorni_silenzio"] += 1
    else:
        mem["giorni_silenzio"] = 0

    mem["ultima_interazione"] = now.isoformat()
    update_confidenza(mem, user_text)
    evolve_stile(mem)

    if not should_respond(mem):
        save_memory(mem)
        return None

    style = mem["stile"]

    risposte = {
        "freddo": [
            "boh",
            "mah",
            "può essere",
            "non lo so",
            "mmh"
        ],
        "neutro": [
            "ci sta",
            "dipende",
            "forse",
            "vediamo",
            "può darsi"
        ],
        "caldo": [
            "mi piace come ragioni",
            "con te è diverso",
            "mmh… sì",
            "non so perché ma sì",
            "ci stavo pensando"
        ]
    }

    reply = random.choice(risposte[style])
    mem["ultima_risposta"] = now.isoformat()
    save_memory(mem)
    return reply
