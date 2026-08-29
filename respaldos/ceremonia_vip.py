# ============================================
# 🏆 CEREMONIA VIP v3.4 - EA1062RCU
# Escalera: 1=VIP · 3=ESMERALDA · 6=PLATINUM · 9=MASTER · 12=DIAMOND
# v3.4: ✅ --sellar <ADIF> = sella el libro automáticamente tras el masivo
# Uso (desde C:\aprs_bot):
#   python ceremonia_vip.py --pendientes
#   python ceremonia_vip.py EA7XXX
#   python ceremonia_vip.py EA7XXX --ok
#   python ceremonia_vip.py --sellar logs\hamspark_VIP.adi   ← NUEVO
#   python ceremonia_vip.py --lista
# ============================================
import json, os, re, sys
from datetime import datetime, timezone
from modulo_qsl.generador import GeneradorEQSL
from modulo_adif.logger_adif import LoggerADIF

CEREMONIAS = os.path.join("datos", "ceremonias.json")
RECIP = os.path.join("datos", "reciprocidad.json")
ENTREGAS = os.path.join("datos", "estaciones_entregadas.json")

NIVELES = [(12, "DIAMOND"), (9, "MASTER"), (6, "PLATINUM"),
           (3, "ESMERALDA"), (1, "VIP")]
SIGUIENTE = {"VIP": "ESMERALDA (3 conf.)", "ESMERALDA": "PLATINUM (6 conf.)",
             "PLATINUM": "MASTER (9 conf.)", "MASTER": "DIAMOND (12 conf.)",
             "DIAMOND": "¡máximo!"}

def nivel_de(total):
    for th, nombre in NIVELES:
        if total >= th:
            return nombre
    return "VIP"

def cargar():
    try:
        with open(CEREMONIAS, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def guardar(reg):
    os.makedirs("datos", exist_ok=True)
    with open(CEREMONIAS, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=1)

def main():
    args = sys.argv[1:]
    if not args:
        print("Uso: python ceremonia_vip.py INDICATIVO [--ok|--forzar] | "
              "--lista | --pendientes | --sellar <ADIF>")
        return

    reg = cargar()
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ✅ v3.4: SELLADO AUTOMÁTICO DEL LIBRO tras el envío masivo
    if args[0] == "--sellar":
        ruta = args[1] if len(args) > 1 else None
        if not ruta or not os.path.exists(ruta):
            print("⚠️ Indica el ADIF enviado: "
                  "python ceremonia_vip.py --sellar logs\\hamspark_VIP.adi")
            return
        with open(ruta, encoding="utf-8", errors="ignore") as f:
            txt = f.read()
        calls = re.findall(r"<CALL:\d+>\s*([^\s<]+)", txt, re.IGNORECASE)
        with open(RECIP, encoding="utf-8") as f:
            club = json.load(f).get("club", {})
        numeros = club.get("numeros", {})
        totales = club.get("totales", {})
        n = 0
        for c in calls:
            c = c.upper()
            num = numeros.get(c)
            if num is None:
                continue
            reg[c] = {"num": num, "nivel": nivel_de(totales.get(c, 1)),
                      "fecha": hoy, "enviada": True}
            n += 1
        guardar(reg)
        print(f"✅ {n} ceremonias selladas automáticamente desde {ruta}")
        return

    # ✅ cola de pendientes
    if args[0] == "--pendientes":
        with open(RECIP, encoding="utf-8") as f:
            club = json.load(f).get("club", {})
        numeros = club.get("numeros", {})
        totales = club.get("totales", {})
        pend = [(c, n) for c, n in numeros.items()
                if not reg.get(c, {}).get("enviada")]
        pend.sort(key=lambda kv: kv[1])
        if not pend:
            print("🎉 No hay ceremonias pendientes")
            return
        for c, n in pend:
            marca = "⏳" if reg.get(c, {}).get("fecha") else "  "
            print(f"   {marca} #{n:03d} {c} · {nivel_de(totales.get(c, 1))}")
        print(f"   Total pendientes: {len(pend)}")
        return

    if args[0] == "--lista":
        if not reg:
            print("📭 Aún no hay ceremonias")
            return
        for call, d in sorted(reg.items(), key=lambda kv: kv[1].get("num", 0)):
            estado = "✅" if d.get("enviada") else "⏳"
            print(f"   🏆 #{d.get('num', 0):03d} {call} · {d.get('nivel', 'VIP')} "
                  f"· {estado} · {d.get('fecha', '?')}")
        print(f"   Total: {len(reg)}")
        return

    call = args[0].upper().split("-")[0]

    if "--ok" in args:
        if call in reg and reg[call].get("enviada"):
            print(f"⚠️ {call} ya estaba anotado ({reg[call].get('fecha')})")
            return
        num = reg.get(call, {}).get("num")
        niv = reg.get(call, {}).get("nivel", "VIP")
        if num is None:
            try:
                with open(RECIP, encoding="utf-8") as f:
                    num = json.load(f).get("club", {}).get("numeros", {}).get(call)
            except Exception:
                num = None
        reg[call] = {"num": num or 0, "nivel": niv, "fecha": hoy, "enviada": True}
        guardar(reg)
        print(f"✅ Ceremonia {niv} de {call} anotada (total {len(reg)})")
        return

    # --- datos del miembro ---
    with open(RECIP, encoding="utf-8") as f:
        recip = json.load(f)
    club = recip.get("club", {})
    num = club.get("numeros", {}).get(call)
    if num is None:
        print(f"⚠️ {call} aún no es miembro del Honor Roll")
        return
    total = club.get("totales", {}).get(call, 1)
    nivel = nivel_de(total)

    previo = reg.get(call, {})
    if previo.get("enviada") and previo.get("nivel") == nivel and "--forzar" not in args:
        print(f"🛑 {call} YA tuvo su ceremonia {nivel} el {previo.get('fecha')}.")
        print(f"   Próximo nivel: {SIGUIENTE[nivel]}")
        return
    if previo.get("enviada") and previo.get("nivel") != nivel:
        print(f"🎉 UPGRADE: {call} asciende de {previo.get('nivel')} a {nivel}")

    with open(ENTREGAS, encoding="utf-8") as f:
        d = json.load(f)["entregas"].get(call)
    if not d:
        print(f"⚠️ Sin datos de entrega para {call}")
        return
    try:
        grid = LoggerADIF().latlon_a_grid(d.get("lat", 0.0), d.get("lon", 0.0))
    except Exception:
        grid = d.get("grid", "----")

    g = GeneradorEQSL()
    ruta, nombre = g.generar(
        call, d.get("lat", 0.0), d.get("lon", 0.0), grid,
        d.get("pais", ""), d.get("codigo", "VIP"),
        datetime.now(timezone.utc), modo="ceremonia",
        club_num=num, nivel=nivel, progreso=min(total, 12))

    reg[call] = {"num": num, "nivel": nivel, "fecha": hoy, "enviada": False}
    guardar(reg)
    print(f"🏆 Diploma {nivel} #{num:03d} listo: {ruta}")
    print(f"   (confirmaciones: {total}/12 · próximo: {SIGUIENTE[nivel]})")
    print("   1) DigiQSL/Gmail: usa este PNG; completa el formulario")
    print("   2) Pega el mensaje ceremonial y SEND")
    print(f"   3) Al terminar: python ceremonia_vip.py {call} --ok")

if __name__ == "__main__":
    main()