# ============================================
# 🛡️ ADIF GUARD v1.1 - EA1062RCU (anti-duplicados + plantilla oficial)
#
# Funciones:
#   dedupe_archivo(ruta)          → elimina duplicados conservando el header
#   fijar_ultimo_comentario(...)  → sobrescribe COMMENT del último registro
#   preparar_subida / marcar_subidas → ledger de idempotencia (opcional)
#
# Uso standalone:
#   python adif_guard.py limpiar logs\mi_adif.adi
# ============================================
import json, os, re, sys

DATOS = "datos"
LEDGER = os.path.join(DATOS, "eqsl_subidas.json")

def _parse_records(text):
    out = []
    for r in re.split(r"<EOR>", text, flags=re.I):
        if not r.strip():
            continue
        def g(tag):
            m = re.search(r"<%s:\d+(?:[^>]*)>\s*([^<]+)" % tag, r, re.I)
            return m.group(1).strip() if m else ""
        out.append({
            "call": g("CALL").upper(),
            "date": g("QSO_DATE"),
            "time": g("TIME_ON"),
            "band": g("BAND"),
            "raw": r.strip() + "\n<EOR>\n",
        })
    return out

def clave(rec):
    return f"{rec['call']}|{rec['date']}|{rec['time']}|{rec['band']}"

def _extraer_header(text):
    m = re.search(r"<EOH>", text, re.I)
    if m:
        return text[:m.end()] + "\n"
    m2 = re.search(r"<CALL:", text, re.I)
    return text[:m2.start()] if m2 else ""

def dedupe_archivo(ruta_adif):
    """Elimina registros duplicados (CALL+DATE+TIME+BAND) conservando
    el header original. Devuelve cantidad de removidos."""
    try:
        with open(ruta_adif, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        return 0
    records = _parse_records(text)
    if not records:
        return 0
    vistos, limpios = set(), []
    for rec in records:
        k = clave(rec)
        if k in vistos:
            continue
        vistos.add(k)
        limpios.append(rec)
    removidos = len(records) - len(limpios)
    if removidos:
        header = _extraer_header(text)
        with open(ruta_adif, "w", encoding="utf-8") as f:
            f.write(header)
            for rec in limpios:
                f.write(rec["raw"])
        print(f"🛡️ ADIF GUARD: {os.path.basename(ruta_adif)} -> "
              f"{removidos} duplicado(s) eliminado(s)")
    return removidos

def fijar_ultimo_comentario(ruta_adif, comentario):
    """Sobrescribe (o inserta) el campo COMMENT del ÚLTIMO registro
    del ADIF, recalculando su longitud."""
    try:
        with open(ruta_adif, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        return False
    idx = text.rfind("<EOR>")
    if idx == -1:
        return False
    prev = text.rfind("<EOR>", 0, idx)
    start = prev + len("<EOR>") if prev != -1 else 0
    seg = text[start:idx]
    nuevo = f"<COMMENT:{len(comentario)}>{comentario}"
    m = re.search(r"<COMMENT:\d+>[^<]*", seg, re.I)
    if m:
        seg2 = seg[:m.start()] + nuevo + seg[m.end():]
    else:
        seg2 = seg.rstrip() + nuevo + "\n"
    text2 = text[:start] + seg2 + text[idx:]
    with open(ruta_adif, "w", encoding="utf-8") as f:
        f.write(text2)
    return True

def _cargar_ledger():
    try:
        return set(json.load(open(LEDGER, encoding="utf-8")))
    except Exception:
        return set()

def _guardar_ledger(s):
    os.makedirs(DATOS, exist_ok=True)
    json.dump(sorted(s), open(LEDGER, "w", encoding="utf-8"), indent=1)

def preparar_subida(ruta_adif, usar_ledger=True):
    text = open(ruta_adif, encoding="utf-8", errors="ignore").read()
    records = _parse_records(text)
    ledger = _cargar_ledger() if usar_ledger else set()
    vistos, limpios, claves = set(), [], []
    for rec in records:
        k = clave(rec)
        if k in vistos or k in ledger:
            continue
        vistos.add(k)
        limpios.append(rec)
        claves.append(k)
    header = _extraer_header(text)
    with open(ruta_adif, "w", encoding="utf-8") as f:
        f.write(header)
        for rec in limpios:
            f.write(rec["raw"])
    print(f"🛡️ ADIF GUARD: {len(records)} registros -> {len(limpios)} limpios "
          f"({len(records) - len(limpios)} bloqueados)")
    return claves

def marcar_subidas(claves):
    if not claves:
        return
    ledger = _cargar_ledger()
    ledger.update(claves)
    _guardar_ledger(ledger)
    print(f"🛡️ ADIF GUARD: {len(claves)} claves registradas en ledger")

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "limpiar":
        dedupe_archivo(sys.argv[2])
    else:
        print("Uso: python adif_guard.py limpiar <archivo.adi>")