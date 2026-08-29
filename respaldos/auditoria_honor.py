# ============================================
# ⚖️ AUDITORÍA HONOR ROLL v2 - EA1062RCU
# Verifica: totales == legado + actas casadas con estrella
# Uso: python auditoria_honor.py
# ============================================
import json, os

DATOS = "datos"
recip = json.load(open(os.path.join(DATOS, "reciprocidad.json"), encoding="utf-8"))
club = recip.get("club", {})
numeros, totales = club.get("numeros", {}), club.get("totales", {})
legado = club.get("legado", {})

try:
    acum = json.load(open(os.path.join(DATOS, "qrz_confirmados.json"), encoding="utf-8"))
except Exception:
    acum = {}

ent = json.load(open(os.path.join(DATOS, "estaciones_entregadas.json"), encoding="utf-8"))
actas = {}
for base, e in ent.get("entregas", {}).items():
    f = (e.get("fecha") or "").replace("-", "")
    if f and e.get("codigo"):
        actas[f"{base}|{f}"] = base

casadas = {}
for k in acum:
    call, fecha = k.split("|")
    if f"{call}|{fecha}" in actas:
        casadas[call] = casadas.get(call, 0) + 1

print("=== AUDITORÍA DX HONOR ROLL v2 ===")
print(f"Miembros: {len(numeros)} · Estrellas acumuladas: {len(acum)}")
print(f"Legado congelado: {legado if legado else 'ninguno'}")
mal = [(c, totales.get(c, 0), legado.get(c, 0) + casadas.get(c, 0))
       for c in numeros
       if totales.get(c, 0) != legado.get(c, 0) + casadas.get(c, 0)]
if mal:
    print("⚠️ Discrepancias (libro vs cruce+legado):")
    for c, t, m in mal:
        print(f"   {c}: libro {t} · esperado {m}")
else:
    print("✅ SIN discrepancias: el libro refleja legado + cruce exacto")
print(f"✅ Miembros verificados: {len(numeros) - len(mal)}/{len(numeros)}")