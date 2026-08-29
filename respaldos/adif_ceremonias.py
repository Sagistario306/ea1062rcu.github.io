# ============================================
# 📜 ADIF CEREMONIAS v1 - EA1062RCU
# Genera el ADIF de los miembros del Honor Roll para hamSpark
# Uso (desde C:\aprs_bot):
#   python adif_ceremonias.py                 → todos (hamspark_TODOS.adi)
#   python adif_ceremonias.py VIP             → solo ese nivel
#   python adif_ceremonias.py --call EA3HMZ   → uno solo (prueba/bautizo)
# ============================================
import json, os, sys

RECIP = os.path.join("datos", "reciprocidad.json")
ENTREGAS = os.path.join("datos", "estaciones_entregadas.json")

NIVELES = [(12, "DIAMOND"), (9, "MASTER"), (6, "PLATINUM"),
           (3, "ESMERALDA"), (1, "VIP")]

def nivel_de(t):
    for th, n in NIVELES:
        if t >= th:
            return n
    return "VIP"

def campo(n, v):
    return f"<{n}:{len(v)}>{v}"

def main():
    args = sys.argv[1:]
    filtro = None
    call_f = None
    if args and args[0] == "--call":
        call_f = args[1].upper() if len(args) > 1 else None
    elif args:
        filtro = args[0].upper()

    with open(RECIP, encoding="utf-8") as f:
        club = json.load(f).get("club", {})
    numeros = club.get("numeros", {})
    totales = club.get("totales", {})
    ingresos = club.get("ingresos", {})
    with open(ENTREGAS, encoding="utf-8") as f:
        ent = json.load(f)["entregas"]

    regs = []
    for call, num in sorted(numeros.items(), key=lambda kv: kv[1]):
        niv = nivel_de(totales.get(call, 1))
        if call_f and call != call_f:
            continue
        if filtro and niv != filtro:
            continue
        d = ent.get(call, {})
        fecha = (d.get("fecha") or ingresos.get(call, "2026-08-01")).replace("-", "")
        regs.append((call, num, niv, fecha))

    if not regs:
        print("⚠️ Sin registros para ese filtro")
        return

    tag = call_f or filtro or "TODOS"
    salida = os.path.join("logs", f"hamspark_{tag}.adi")
    os.makedirs("logs", exist_ok=True)
    with open(salida, "w", encoding="utf-8") as f:
        f.write("EA1062RCU DX HONOR ROLL - ADIF para hamSpark\n<EOH>\n")
        for call, num, niv, fecha in regs:
            com = (f"DX HONOR ROLL #{num:03d} NIVEL {niv} · "
                   f"tinyurl.com/ea1062rcu · 73")
            f.write(campo("CALL", call) + campo("QSO_DATE", fecha) +
                    campo("TIME_ON", "1200") + campo("BAND", "2M") +
                    campo("MODE", "PKT") + campo("RST_SENT", "59") +
                    campo("STATION_CALLSIGN", "EA1062RCU") +
                    campo("COMMENT", com) + "<EOR>\n")

    print(f"📜 {len(regs)} registro(s) en {salida}")
    for call, num, niv, fecha in regs[:6]:
        print(f"   #{num:03d} {call} · {niv}")
    print("   hamSpark: paso 1 = fondo del nivel · paso 2 = este ADIF")

if __name__ == "__main__":
    main()