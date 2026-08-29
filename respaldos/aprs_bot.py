# ============================================
# 🤖 NÚCLEO BOT APRS v4.9 - EA1062RCU (MODO SWL PURO + DX HONOR ROLL)
# v3.25: 7 capas + ED hermético + PAISES_SIN_MENSAJE
# v3.26: RECIPROCIDAD: retenidas hasta confirmar QRZ
# v3.27: limpieza automática de carpeta local
# v3.28: cortesía RF (1 intento · sin recordatorios · tope)
# v3.29: nunca silencioso (latido/minuto + aviso RX)
# v3.30: anti auto-responder (AFK)
# v4.0:  MODO SWL PURO: CERO transmisiones · solo recepción + web/QRZ
# v4.1:  RX inteligente (rotación + solo lectura)
# v4.2:  ✅ DX HONOR ROLL: tarjeta dorada VIP + club_index.json público
# v4.3:  ✅ club_index incluye NIVEL calculado (RX probado con passcode real)
# v4.4:  🛡️ ADIF GUARD: dedupe del ADIF completo + comentario oficial
# v4.6:  🩹 RX restaurado a lógica v4.3 (pass -1 rechazado por servidor)
#        + clasifica "password" como error de login
# v4.7:  🚫 lista de exclusión (opt-out) — respeta eQSL/ADIF/mensajes en vivo
#        + precarga de excluidas ANTES del banner (conteo veraz)
# v4.8:  🎴 1 QSO/estación/mes (el QSO es el determinante, nunca repetitivo)
#        + evento dual: 2 tarjetas (mensual+evento) en 1 QSO con 2 códigos
#        + Regla 3: si ya tiene QSO del mes → no participa del evento
# v4.9:  🛡️ micro-blindaje: el evento falla en su propio try/except →
#        el ADIF SIEMPRE se escribe (QSO mensual garantizado)
# ============================================
import os
import json
import time
import socket
import threading
import unicodedata
from datetime import datetime, timezone

import aprslib
import adif_guard

from config import *
from modulo_qsl.codigos import GestorCodigos
from modulo_qsl.generador import GeneradorEQSL
from modulo_adif.logger_adif import LoggerADIF
from modulo_github.publicador import PublicadorGitHub
from modulo_notificaciones.aprs_mensajes import GestorMensajesAPRS
from modulo_notificaciones.telegram import NotificadorTelegram

try:
    URL_EQSL
except NameError:
    URL_EQSL = "sagistario306.github.io/ea1062rcu.github.io/eqsl.html"

# 🛡️ v4.4: URL recortada oficial para el comentario eQSL
URL_CORTA = globals().get("URL_CORTA", "tinyurl.com/ea1062rcu")

MES_ABREV = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
             "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

SIMBOLOS = {"antena": "&", "casa": "-", "telefono": "$",
            "clima": "_", "digi": "#", "igate": "I"}

SIMBOLOS_INFRA = {"_", "#"}
CLAVES_INFRA = ("IGATE", "I-GATE", "DIGI", "MMDVM", "LORA", "RNG0001",
                "WEATHER", "WX", "CWOP", "METEO", "VOICE", "TELEMETRY",
                "ESP8266", "ESP32", "PCBUNIT", "MESHTASTIC", "WL:", "BANJIR",
                "REPETIDOR", "REPEATER", "RPT", "TONO", "TONE", "INTBAT",
                "RD625", "DMR", "CC1")

def _norm_txt(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", str(s))
        if unicodedata.category(c) != "Mn"
    ).lower()

def passcode(indicativo):
    call = indicativo.split("-")[0].upper()
    h = 0x73e2
    i = 0
    while i < len(call):
        h ^= ord(call[i]) << 8
        if i + 1 < len(call):
            h ^= ord(call[i + 1])
        i += 2
    return h & 0x7FFF

_PREFIJOS = []
for _pais, _prefs in PAISES_FASE_1.items():
    _PREFIJOS += [(p, _pais) for p in _prefs]
if ACTIVAR_FASE_2:
    for _pais, _prefs in PAISES_FASE_2.items():
        _PREFIJOS += [(p, _pais) for p in _prefs]
PREFIJOS_ORDENADOS = sorted(_PREFIJOS, key=lambda t: len(t[0]), reverse=True)

class BotAPRS:
    def __init__(self):
        self.codigos = GestorCodigos(ARCHIVO_ENTREGAS)
        self.generador = GeneradorEQSL()
        self.adif = LoggerADIF()
        self.publicador = PublicadorGitHub(GITHUB_TOKEN)
        try:
            self.mensajes = GestorMensajesAPRS(
                CALLSIGN, passcode(CALLSIGN),
                max_dia=globals().get("MENSAJES_MAX_DIA", 120))
        except TypeError:
            self.mensajes = GestorMensajesAPRS(CALLSIGN, passcode(CALLSIGN))
        self.telegram = NotificadorTelegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

        try:
            with open("datos/ssid_map.json", encoding="utf-8") as f:
                self.ssid_map = json.load(f)
        except Exception:
            self.ssid_map = {}

        try:
            with open("datos/buzon_map.json", encoding="utf-8") as f:
                self.buzon_map = json.load(f)
        except Exception:
            self.buzon_map = {}

        try:
            with open("datos/afk_map.json", encoding="utf-8") as f:
                self.afk = set(json.load(f))
        except Exception:
            self.afk = set()

        hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.fecha_actual = hoy
        self.eqsl_hoy = 0
        self.nuevas_hoy = 0
        for _d in self.codigos.entregas["entregas"].values():
            if str(_d.get("fecha", "")).startswith(hoy):
                self.eqsl_hoy += 1
                self.nuevas_hoy += 1
            for _evd in _d.get("eventos", {}).values():
                if str(_evd.get("fecha", "")).startswith(hoy):
                    self.eqsl_hoy += 1

        self.pais_hoy = {}
        for _d in self.codigos.entregas["entregas"].values():
            if str(_d.get("fecha", "")).startswith(hoy):
                _p = _d.get("pais", "")
                if _p:
                    self.pais_hoy[_p] = self.pais_hoy.get(_p, 0) + 1

        self._cuotas_norm = {
            _norm_txt(k): v
            for k, v in globals().get("CUOTAS_POR_PAIS", {}).items()
        }

        self.recip = self._cargar_reciprocidad()
        self.recip_bloq = set(self.recip.get("bloqueadas", []))
        self._rollover_reciprocidad()

        # ✅ v4.2: DX HONOR ROLL (miembros VIP)
        club = self.recip.get("club", {})
        self.club_num = club.get("numeros", {})
        self.club_tot = club.get("totales", {})
        self.club_ing = club.get("ingresos", {})

        self._rec_file = f"datos/recordados_{hoy}.json"
        try:
            with open(self._rec_file, encoding="utf-8") as f:
                self.recordados_hoy = set(json.load(f))
        except Exception:
            self.recordados_hoy = set()

        self.adif_hoy = set()
        self.auto_hoy = set()
        self.auto_cool = {}
        self.fase2_hoy = {}
        self._cuota_aviso = set()
        self.dx_del_dia = []
        self.rx_vistas = 0
        self.infra_vistas = 0
        self.dbg = 50
        self.pendientes = []
        self._tope_aviso = False
        self.rx_conn = None
        self._rx_last = time.time()
        self._rx_fallos = 0
        self._rx_count = 0
        self._rx_host_idx = 0
        self._rx_quick = 0
        self._rx_up = 0.0

        # 🚫 v4.7: lista de exclusión (opt-out por petición propia)
        self._excl_ts = 0.0
        self.excluidas = set()

    # ==========================================
    # 🚫 EXCLUSIÓN (opt-out) v4.7
    # ==========================================
    def _cargar_excluidas(self):
        if time.time() - self._excl_ts < 60:
            return
        self._excl_ts = time.time()
        try:
            with open("datos/excluidas.json", encoding="utf-8") as f:
                self.excluidas = set(str(x).upper() for x in json.load(f))
        except Exception:
            self.excluidas = set()

    # ==========================================
    # RECIPROCIDAD (v3.26)
    # ==========================================
    def _cargar_reciprocidad(self):
        try:
            with open("datos/reciprocidad.json", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"confirmadas": {}, "bloqueadas": []}

    def _guardar_reciprocidad(self):
        os.makedirs("datos", exist_ok=True)
        tmp = "datos/reciprocidad.json.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.recip, f, ensure_ascii=False, indent=1)
        os.replace(tmp, "datos/reciprocidad.json")

    def _rollover_reciprocidad(self):
        ahora = datetime.now(timezone.utc)
        mes_act = ahora.strftime("%Y-%m")
        conf = self.recip.get("confirmadas", {})
        bloq = set(self.recip.get("bloqueadas", []))
        camb = False
        for base, d in self.codigos.entregas["entregas"].items():
            m = str(d.get("mes", ""))
            if m and m < mes_act and base not in conf and base not in bloq:
                bloq.add(base)
                camb = True
        for b in list(bloq):
            if b in conf:
                bloq.discard(b)
                camb = True
        self.recip["bloqueadas"] = sorted(bloq)
        self.recip_bloq = bloq
        if camb:
            self._guardar_reciprocidad()

    # ==========================================
    # ✅ v4.3 DX HONOR ROLL (con niveles calculados)
    # ==========================================
    def _club_index(self):
        out = []
        niveles = [(12, "DIAMOND"), (9, "MASTER"), (6, "PLATINUM"),
                   (3, "ESMERALDA"), (1, "VIP")]
        def nivel_de(t):
            for th, n in niveles:
                if t >= th:
                    return n
            return "VIP"

        for call, n in self.club_num.items():
            total = self.club_tot.get(call, 1)
            out.append({
                "num": n,
                "indicativo": call,
                "nivel": nivel_de(total),
                "ingreso": self.club_ing.get(call, ""),
                "total": total,
            })
        return out

    def _publicar_club(self):
        try:
            import base64
            import requests
            url = f"https://api.github.com/repos/{REPO_GITHUB}/contents/club_index.json"
            headers = {"Authorization": f"token {GITHUB_TOKEN}",
                       "Accept": "application/vnd.github.v3+json"}
            r = requests.get(url, headers=headers, timeout=15)
            sha = r.json().get("sha") if r.status_code == 200 else None
            body = {
                "message": "DX HONOR ROLL update",
                "content": base64.b64encode(json.dumps(
                    self._club_index(), ensure_ascii=False,
                    indent=1).encode()).decode(),
            }
            if sha:
                body["sha"] = sha
            q = requests.put(url, headers=headers, json=body, timeout=20)
            print(f"🏆 DX HONOR ROLL publicado: {len(self.club_num)} miembros "
                  f"(HTTP {q.status_code})")
        except Exception as e:
            print(f"⚠️ Club no publicado: {e}")

    # ==========================================
    # AUTO-RESPONDERS (v3.30)
    # ==========================================
    def _guardar_afk(self):
        try:
            os.makedirs("datos", exist_ok=True)
            with open("datos/afk_map.json", "w", encoding="utf-8") as f:
                json.dump(sorted(self.afk), f)
        except Exception:
            pass

    def _es_auto_msg(self, txt):
        low = txt.lower()
        if low.startswith("aa:") or "[aa]" in low:
            return True
        return any(p in low for p in ("away from keyboard", "leave your messages",
                                      "tnx ur msg", "auto message", "auto-reply"))

    def _enviar_msg(self, ind, texto, prioridad=False):
        if globals().get("MODO_SWL_PURO", False):
            return False
        try:
            return self.mensajes.enviar_mensaje(ind, texto, prioridad=prioridad)
        except TypeError:
            return self.mensajes.enviar_mensaje(ind, texto)

    # ==========================================
    # UTILIDADES
    # ==========================================
    def construir_filtro(self):
        prefijos = []
        for prefs in PAISES_FASE_1.values():
            prefijos += prefs
        if ACTIVAR_FASE_2:
            for prefs in PAISES_FASE_2.values():
                prefijos += prefs
        return " ".join(f"p/{p}" for p in prefijos)

    def detectar_pais(self, indicativo):
        base = indicativo.split("-")[0].upper()
        for pref, pais in PREFIJOS_ORDENADOS:
            if base.startswith(pref):
                return pais
        return None

    def _es_infra(self, paquete):
        ind = str(paquete.get("from", "")).upper()
        base = ind.split("-")[0]
        if base and not any(c.isdigit() for c in base):
            return True
        if paquete.get("weather"):
            return True
        sym_c = paquete.get("symbolcode", "")
        sym_t = paquete.get("symboltable", "")
        if sym_c in SIMBOLOS_INFRA:
            return True
        if sym_t == "\\" and sym_c == "R":
            return True
        if ind.endswith("-WX") or ind.endswith("-R"):
            return True
        if len(base) >= 3 and base.startswith("ED") and base[2].isdigit():
            return True
        com = str(paquete.get("comment", "")).upper()
        return any(k in com for k in CLAVES_INFRA)

    def _recordar_ssid(self, base, ind):
        if ind and ind != self.ssid_map.get(base):
            self.ssid_map[base] = ind
            try:
                os.makedirs("datos", exist_ok=True)
                with open("datos/ssid_map.json", "w", encoding="utf-8") as f:
                    json.dump(self.ssid_map, f, ensure_ascii=False)
            except Exception:
                pass

    def _recordar_buzon(self, base, ind):
        if ind and ind != self.buzon_map.get(base):
            self.buzon_map[base] = ind
            try:
                os.makedirs("datos", exist_ok=True)
                with open("datos/buzon_map.json", "w", encoding="utf-8") as f:
                    json.dump(self.buzon_map, f, ensure_ascii=False)
                print(f"📬 Buzón humano aprendido: {base} → {ind}")
            except Exception:
                pass

    def _buzon(self, base):
        return self.buzon_map.get(base) or self.ssid_map.get(base, base)

    def _marcar_recordado(self, base):
        self.recordados_hoy.add(base)
        try:
            os.makedirs("datos", exist_ok=True)
            with open(self._rec_file, "w", encoding="utf-8") as f:
                json.dump(list(self.recordados_hoy), f)
        except Exception:
            pass

    def _auto_respuesta(self, base, ind, forzada=False):
        if globals().get("MODO_SWL_PURO", False):
            return
        if base in self.afk:
            return
        ahora = time.time()
        if forzada:
            if ahora - self.auto_cool.get(base, 0) < 600:
                return
            self.auto_cool[base] = ahora
        else:
            if base in self.auto_hoy:
                return
            self.auto_hoy.add(base)
        if base in self.recip_bloq:
            self._enviar_msg(
                ind, f"eQSL on hold. Log {CALLSIGN} on QRZ.com to reactivate. 73",
                prioridad=True)
            print(f"🔒 {ind}: aviso de reciprocidad enviado")
            return
        info = self.codigos.obtener_info_entrega(base)
        if info and info.get("codigo"):
            # 🛡️ v4.4: plantilla oficial unificada
            self._enviar_msg(
                ind, f"CONFIRM COD {info['codigo']} {URL_CORTA} QRZ 73",
                prioridad=True)
            print(f"🤖 Auto-ayuda enviada a {ind}")
        else:
            self._enviar_msg(
                ind, f"No eQSL yet this month. Keep on air! {URL_CORTA} 73",
                prioridad=True)
            print(f"🤖 Ayuda general enviada a {ind}")

    def tope_activo(self):
        ev = self.generador.evento_activo(datetime.now(timezone.utc))
        if ev and "tope_evento" in ev:
            return min(int(ev["tope_evento"]), TOPE_DURO)
        return min(TOPE_GLOBAL_DIARIO, TOPE_DURO)

    def _aviso_tope(self):
        if not self._tope_aviso:
            self._tope_aviso = True
            print(f"🛑 Tope diario alcanzado ({self.tope_activo()})")

    def _rotar_dia(self):
        hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if hoy != self.fecha_actual:
            self.fecha_actual = hoy
            self.eqsl_hoy = 0
            self.nuevas_hoy = 0
            self.adif_hoy = set()
            self.recordados_hoy = set()
            self.auto_hoy = set()
            self.auto_cool = {}
            self.pais_hoy = {}
            self._cuota_aviso = set()
            self._rec_file = f"datos/recordados_{hoy}.json"
            self.fase2_hoy = {}
            self.dx_del_dia = []
            self._tope_aviso = False
            if hoy.endswith("-01"):
                self._rollover_reciprocidad()
                self._limpieza_mensual()

    # ==========================================
    # WATCHDOG + LATIDO (v3.29)
    # ==========================================
    def _bucle_watchdog(self):
        while True:
            time.sleep(30)
            if self.rx_conn is not None and time.time() - self._rx_last > 120:
                print("🐕 Watchdog: RX mudo >120 s → forzando reconexión")
                try:
                    self.rx_conn.sock.close()
                except Exception:
                    pass

    def _bucle_latido(self):
        ciclos = 0
        while True:
            time.sleep(60)
            ciclos += 1
            if self.rx_conn is None:
                print(f"💓 RX reconectando · eQSL hoy "
                      f"{self.eqsl_hoy}/{self.tope_activo()} · "
                      f"{datetime.now(timezone.utc).strftime('%H:%M')} UTC")
                continue
            if ciclos % 5 == 0:
                print(f"💓 RX activo · {self._rx_count} paquetes en 5 min · "
                      f"eQSL hoy {self.eqsl_hoy}/{self.tope_activo()}")
                self._rx_count = 0

    def _bucle_rx(self, conexion):
        sock = conexion.sock
        sock.settimeout(60)
        buffer = b""
        while True:
            try:
                data = sock.recv(4096)
            except socket.timeout:
                continue
            except Exception as e:
                raise ConnectionError(f"RX socket: {e}")
            if not data:
                raise ConnectionError("servidor cerró la conexión")
            buffer += data
            while b"\n" in buffer:
                linea, buffer = buffer.split(b"\n", 1)
                self.al_recibir_linea(linea)

    def _indice_web(self):
        mes = datetime.now(timezone.utc).strftime("%Y-%m")
        out = []
        for ind, d in self.codigos.entregas["entregas"].items():
            base = ind.split("-")[0].upper()
            if d.get("mes") == mes and d.get("codigo"):
                arch = d.get("archivo") or f"qsl/QSL_{ind}_{mes}.png"
                out.append({
                    "indicativo": base,
                    "codigo": d["codigo"],
                    "fecha": d["fecha"],
                    "pais": d["pais"],
                    "archivo": arch,
                })
            for ev_id, evd in d.get("eventos", {}).items():
                if str(evd.get("fecha", "")).startswith(mes):
                    arch = evd.get("archivo") or f"qsl/QSL_{ind}_{mes}_EV.png"
                    out.append({
                        "indicativo": base,
                        "codigo": evd["codigo"],
                        "fecha": evd["fecha"],
                        "pais": d.get("pais", ""),
                        "archivo": arch,
                    })
        return out

    def _publicar_tarjeta(self, ruta, nombre):
        if self.publicador.publicar_eqsl(ruta, nombre):
            self.publicador.publicar_indice(self._indice_web())
        else:
            self.pendientes.append((ruta, nombre))
            self.publicador.publicar_indice(self._indice_web())

    def _bucle_reintentos(self):
        while True:
            time.sleep(60)
            if not self.pendientes:
                continue
            ruta, nombre = self.pendientes[0]
            if self.publicador.publicar_eqsl(ruta, nombre):
                self.pendientes.pop(0)
                self.publicador.publicar_indice(self._indice_web())
                print("🔁 Repuesto en GitHub:", nombre)
            else:
                print("⏳ Aún pendiente:", nombre)

    def _bucle_beacon(self):
        if globals().get("MODO_SWL_PURO", False):
            return
        if not globals().get("BEACON_ACTIVO", False):
            return
        while True:
            try:
                cod = SIMBOLOS.get(globals().get("BEACON_SIMBOLO", "antena"), "&")
                lat = globals().get("BEACON_LAT", "1142.00N")
                lon = globals().get("BEACON_LON", "07012.00W")
                com = globals().get("BEACON_COMENTARIO", "EA1062RCU SWL eQSL Bot")
                raw = f"{CALLSIGN}>APRS,TCPIP*:!{lat}/{lon}{cod} {com}"
                sock = getattr(self.rx_conn, "sock", None) if self.rx_conn else None
                if sock is None:
                    time.sleep(60)
                    continue
                sock.sendall((raw + "\r\n").encode())
                print("🗼 Baliza enviada (antena)")
            except Exception as e:
                print("⚠️ Baliza:", e)
                time.sleep(60)
                continue
            time.sleep(globals().get("BEACON_MINUTOS", 30) * 60)

    # ==========================================
    # FLUJOS DE ENTREGA (v4.2: dorada para VIP)
    # ==========================================
    def _intentar_nueva_eqsl(self, base, ind, lat, lon, pais, ahora):
        if base in self.recip_bloq:
            print(f"🔒 {base}: eQSL retenida por reciprocidad (sin confirmar QRZ)")
            return None
        if pais in PAISES_FASE_2:
            if self.fase2_hoy.get(pais, 0) >= TOPE_POR_PAIS_FASE_2:
                return None
        clave = _norm_txt(pais)
        if clave in self._cuotas_norm:
            if self.pais_hoy.get(pais, 0) >= self._cuotas_norm[clave]:
                if pais not in self._cuota_aviso:
                    self._cuota_aviso.add(pais)
                    print(f"⚖️ Cuota diaria de {pais} alcanzada ({self._cuotas_norm[clave]})")
                return None
        if self.eqsl_hoy >= self.tope_activo():
            self._aviso_tope()
            return None

        codigo = self.codigos.generar_codigo()
        grid = self.adif.latlon_a_grid(lat, lon)
        ruta, nombre = self.generador.generar(
            base, lat, lon, grid, pais, codigo, ahora, modo="mensual",
            club_num=self.club_num.get(base))
        self.codigos.registrar_entrega(base, codigo, lat, lon, pais)
        try:
            self.codigos.entregas["entregas"][base]["archivo"] = f"qsl/{nombre}"
            self.codigos.entregas["entregas"][base]["ultimo_ind"] = ind
        except Exception:
            pass
        self._publicar_tarjeta(ruta, nombre)
        if globals().get("MODO_SWL_PURO", False):
            print(f"📴 {base} ({pais}): tarjeta publicada · SIN mensaje (MODO SWL PURO)"
                  + (f" · 🏆 #{self.club_num[base]:03d}" if base in self.club_num else ""))
        elif pais in globals().get("PAISES_SIN_MENSAJE", []):
            print(f"🔇 {base} ({pais}): tarjeta publicada SIN mensaje APRS (protección RF)")
        elif base in self.afk:
            print(f"🤖 {base}: auto-responder → tarjeta solo en web (sin mensaje)")
        else:
            self.mensajes.notificar_eqsl(ind, codigo)

        self.eqsl_hoy += 1
        self.nuevas_hoy += 1
        self.pais_hoy[pais] = self.pais_hoy.get(pais, 0) + 1
        if pais in PAISES_FASE_2:
            self.fase2_hoy[pais] = self.fase2_hoy.get(pais, 0) + 1
        self.dx_del_dia.append((base, pais))
        print(f"🎴 eQSL {self.eqsl_hoy}/{self.tope_activo()} → {base} ({pais}) cod {codigo}")
        return codigo

    def _intentar_nueva_eqsl_evento(self, base, ind, lat, lon, pais, ahora, ev, ev_id):
        if base in self.recip_bloq:
            return None
        if self.eqsl_hoy >= self.tope_activo():
            self._aviso_tope()
            return None

        codigo = self.codigos.generar_codigo()
        grid = self.adif.latlon_a_grid(lat, lon)
        ruta, nombre = self.generador.generar(
            base, lat, lon, grid, pais, codigo, ahora, modo="evento",
            club_num=self.club_num.get(base))
        self.codigos.registrar_entrega_evento(base, codigo, ev_id, lat, lon, pais)
        try:
            self.codigos.entregas["entregas"][base]["eventos"][ev_id]["archivo"] = f"qsl/{nombre}"
        except Exception:
            pass
        self._publicar_tarjeta(ruta, nombre)
        if not globals().get("MODO_SWL_PURO", False):
            if pais in globals().get("PAISES_SIN_MENSAJE", []):
                print(f"🔇 {base} ({pais}): BONUS SIN mensaje APRS (protección RF)")
            elif base not in self.afk:
                self.mensajes.notificar_eqsl(ind, codigo)

        self.eqsl_hoy += 1
        self.nuevas_hoy += 1
        self.dx_del_dia.append((base, pais))
        print(f"🎁 BONUS {ev_id} → {base} ({pais}) cod {codigo}")
        return codigo

    # ==========================================
    # RECEPCIÓN
    # ==========================================
    def al_recibir_linea(self, linea):
        self._rx_last = time.time()
        self._rx_count += 1
        if isinstance(linea, bytes):
            linea = linea.decode("utf-8", "ignore")
        if self.rx_vistas < 20:
            self.rx_vistas += 1
            print("📡 rx:", linea[:100])
        try:
            paquete = aprslib.parse(linea)
        except Exception as e:
            if self.dbg > 0 and not linea.startswith("#"):
                self.dbg -= 1
                print("🚫 parse:", str(e)[:40], "|", linea[:70])
            return
        self.al_recibir(paquete)

    def al_recibir(self, paquete):
        try:
            ind = paquete.get("from", "")
            base = ind.split("-")[0].upper()

            if base == CALLSIGN.split("-")[0].upper():
                return

            # 🚫 v4.7: exclusión por petición propia (ni eQSL, ni ADIF, ni msg)
            self._cargar_excluidas()
            if base in self.excluidas:
                return

            if paquete.get("format") == "message":
                dest = str(paquete.get("addressee", "")).strip()
                if dest.split("-")[0].upper() == CALLSIGN.split("-")[0].upper():
                    txt = str(paquete.get("message_text", "")).strip()
                    low = txt.lower()
                    if low.startswith("ack") or low.startswith("rej"):
                        return
                    if self._es_auto_msg(txt):
                        if base not in self.afk:
                            self.afk.add(base)
                            self._guardar_afk()
                            print(f"🤖 {base}: auto-responder detectado → "
                                  f"silencio de mensajes (tarjeta solo web)")
                        return
                    if base in self.afk:
                        self.afk.discard(base)
                        self._guardar_afk()
                        print(f"📬 {base}: mensaje humano real → reactivado")
                    self._recordar_buzon(base, ind)
                    clave = any(k in low for k in ("ayuda", "help", "codigo", "code", "?"))
                    self._auto_respuesta(base, ind, forzada=clave)
                return

            lat = paquete.get("latitude")
            lon = paquete.get("longitude")

            if self.dbg > 0:
                self.dbg -= 1
                print(f"🔎 {ind} fmt={paquete.get('format')} lat={lat}")

            if lat is None or lon is None:
                return

            ahora = datetime.now(timezone.utc)
            self._rotar_dia()

            pais = self.detectar_pais(base)
            if pais is None:
                if self.dbg > 0:
                    self.dbg -= 1
                    print("🚫 pais None:", ind)
                return

            self._recordar_ssid(base, ind)

            infra = self._es_infra(paquete) and base not in self.buzon_map

            info = self.codigos.obtener_info_entrega(base)
            entregada = info is not None and info["mes"] == ahora.strftime("%Y-%m")

            # 🚫 v4.8 REGLA 3: ya tiene QSO del mes → no repite, no entra al evento
            if entregada:
                if base not in self.recordados_hoy:
                    self._marcar_recordado(base)
                    if (globals().get("RECORDATORIOS_RF", False)
                            and not globals().get("MODO_SWL_PURO", False)
                            and not infra
                            and pais not in globals().get("PAISES_SIN_MENSAJE", [])
                            and base not in self.afk):
                        self.mensajes.recordar_entregada(
                            self._buzon(base), MES_ABREV[ahora.month - 1],
                            ahora.strftime("%d-%m"), info["codigo"])
                return

            # 🚷 Infra sin operador: ni mensual ni evento
            if infra:
                if self.infra_vistas < 20:
                    self.infra_vistas += 1
                    print(f"🚷 Infra sin operador: {ind} "
                          f"(sym {paquete.get('symbolcode', '?')}) — sin entrega")
                return

            # 🎴 v4.8: primera escucha del mes; si hay evento activo → entrega dual
            ev = self.generador.evento_activo(ahora)
            ev_id = ev.get("id", ev.get("nombre_corto", "evento")) if ev else None

            codigo_mensual = self._intentar_nueva_eqsl(base, ind, lat, lon, pais, ahora)
            codigo_evento = None
            if (codigo_mensual and ev_id
                    and not self.codigos.ya_entregado_evento(base, ev_id)):
                # 🛡️ v4.9: el evento falla en su propio try/except →
                # el ADIF SIEMPRE se escribe con el código mensual
                try:
                    codigo_evento = self._intentar_nueva_eqsl_evento(
                        base, ind, lat, lon, pais, ahora, ev, ev_id)
                    if codigo_evento:
                        print(f"🎁 {base}: QSO mixto mensual+evento "
                              f"({codigo_mensual}; {codigo_evento})")
                except Exception as e:
                    codigo_evento = None
                    print(f"⚠️ Evento falló para {base} "
                          f"({type(e).__name__}: {e}) · se conserva QSO mensual con ADIF")

            if codigo_mensual:
                self._marcar_recordado(base)

            # 🛡️ v4.8: UN SOLO QSO por estación, con 1 o 2 códigos
            if codigo_mensual and base not in self.adif_hoy:
                self.adif_hoy.add(base)
                if codigo_evento:
                    comentario = (f"CONFIRM COD {codigo_mensual}; {codigo_evento} "
                                  f"{URL_CORTA} QRZ 73")
                else:
                    comentario = f"CONFIRM COD {codigo_mensual} {URL_CORTA} QRZ 73"
                self.adif.agregar_contacto(base, lat, lon, codigo_mensual, pais)
                try:
                    adif_guard.fijar_ultimo_comentario(
                        self.adif.ruta_completo, comentario)
                except Exception as e:
                    print(f"⚠️ Comentario ADIF: {e}")

        except Exception as e:
            print("⚠️ Error procesando paquete:", type(e).__name__, "-", e)

    # ==========================================
    # LIMPIEZA MENSUAL (v3.27)
    # ==========================================
    def _limpieza_local(self):
        ahora = datetime.now(timezone.utc)
        meses_local = MESES_EN_LINEA + 1
        carpeta = globals().get("CARPETA_QSL", "eqsl_generadas")
        borrados = 0
        conservados = 0
        try:
            for nombre in os.listdir(carpeta):
                if not nombre.lower().endswith(".png"):
                    continue
                try:
                    ym = nombre.replace(".png", "").replace("_EV", "").split("_")[-1]
                    año, mes = map(int, ym.split("-"))
                    edad = (ahora.year - año) * 12 + (ahora.month - mes)
                except Exception:
                    conservados += 1
                    continue
                if edad > meses_local:
                    try:
                        os.remove(os.path.join(carpeta, nombre))
                        borrados += 1
                    except Exception:
                        pass
                else:
                    conservados += 1
        except Exception as e:
            print(f"⚠️ Limpieza local: {e}")
            return
        print(f"🧹 Local {carpeta}: {borrados} PNGs borrados · "
              f"{conservados} conservados (buffer {meses_local} meses)")

    def _limpieza_mensual(self):
        print("🧹 Limpieza mensual automática...")
        self.codigos.limpiar_antiguas(MESES_EN_LINEA)
        ahora = datetime.now(timezone.utc)
        viejas = []
        for r in self.publicador.listar_carpeta("qsl"):
            try:
                ym = r.replace(".png", "").replace("_EV", "").split("_")[-1]
                año, mes = map(int, ym.split("-"))
                if (ahora.year - año) * 12 + (ahora.month - mes) > MESES_EN_LINEA:
                    viejas.append(r)
            except Exception:
                continue
        if viejas:
            self.publicador.limpiar_eqsl_antiguas(viejas)
        self._limpieza_local()

    # ==========================================
    # RESUMEN TELEGRAM (+ club)
    # ==========================================
    def _bucle_resumen(self):
        ultimo = ""
        while True:
            time.sleep(30)
            ahora = datetime.now(timezone.utc)
            if ahora.strftime("%H:%M") >= HORA_RESUMEN_DIARIO and ultimo != ahora.strftime("%Y-%m-%d"):
                ultimo = ahora.strftime("%Y-%m-%d")
                self._enviar_resumen(ahora)

    def _enviar_resumen(self, ahora):
        stats = self.codigos.obtener_estadisticas()
        dx = "-"
        if self.dx_del_dia:
            ind, pais = min(self.dx_del_dia, key=lambda t: stats["paises"].get(t[1], 1))
            dx = f"{ind} ({pais})"
        # 🛡️ v4.4: dedupe del ADIF completo ANTES de publicar (anti-duplicados eQSL)
        try:
            adif_guard.dedupe_archivo(self.adif.ruta_completo)
        except Exception as e:
            print(f"⚠️ ADIF GUARD: {e}")
        self.telegram.resumen_diario({
            "nuevas_hoy": self.nuevas_hoy,
            "total_mes": stats["total_mes"],
            "paises": len(stats["paises"]),
            "dx_destacado": dx,
            "adif_total": self.adif.srx,
            "eqsl_hoy": self.eqsl_hoy,
            "tope": self.tope_activo(),
        })
        self.publicador.publicar_adif(self.adif.ruta_completo)
        self.publicador.publicar_estadisticas({
            "fecha": ahora.strftime("%Y-%m-%d"),
            "total_mes": stats["total_mes"],
            "paises": stats["paises"],
            "descargadas": stats["descargadas"],
            "pendientes": stats["pendientes"],
        })
        self._publicar_club()

    # ==========================================
    # ARRANQUE + RX inteligente (v4.1 + 🩹 v4.6 + 🛡️ v4.9)
    # ==========================================
    def iniciar(self):
        # 🚫 v4.7: precargar ANTES del banner para mostrar el conteo real
        self._cargar_excluidas()

        cuotas_config = globals().get("CUOTAS_POR_PAIS", {})
        llevadas = []
        for pais_nombre, cuota_lim in cuotas_config.items():
            clave = _norm_txt(pais_nombre)
            real = 0
            for p_real, c in self.pais_hoy.items():
                if _norm_txt(p_real) == clave:
                    real = c
                    break
            llevadas.append(f"{pais_nombre}: {real}/{cuota_lim}")

        print("=" * 60)
        print(f"🤖 BOT APRS v4.9 · {CALLSIGN} · Sistema eQSL Coleccionable")
        print(f"🌍 Países FASE 1: {len(PAISES_FASE_1)} | FASE 2: {'ACTIVA' if ACTIVAR_FASE_2 else 'inactiva'}")
        print(f"⚙️ Tope diario: {self.tope_activo()} | Política: {MESES_EN_LINEA} meses en línea")
        print(f"⚖️ Ya llevadas hoy: {{ {', '.join(llevadas)} }}")
        print(f"🔗 Web: {URL_EQSL}")
        print(f"🛡️ Filtro SOLO HUMANOS: 7 capas + bloque ED hermético")
        print(f"🛡️ ADIF GUARD v1.1: dedupe + plantilla CONFIRM COD activo")
        print(f"🔁 Reciprocidad: {len(self.recip.get('confirmadas', {}))} al día · "
              f"{len(self.recip_bloq)} retenidas")
        print(f"🏆 DX HONOR ROLL: {len(self.club_num)} miembros")
        print(f"🚫 Excluidas (opt-out): {len(self.excluidas)} estaciones")
        print(f"🎴 Política v4.8: 1 QSO/estación/mes · evento dual en primera semana")
        print(f"🛡️ Blindaje v4.9: evento en try/except · ADIF siempre garantizado")
        print(f"🤖 Anti auto-responder: {len(self.afk)} en silencio permanente")
        print(f"🧹 Limpieza local: automática el día 1 (buffer {MESES_EN_LINEA + 1} meses)")
        print(f"💓 Latido visible: cada minuto en reconexión · cada 5 min activo")
        if globals().get("MODO_SWL_PURO", False):
            print("📴 MODO SWL PURO: CERO transmisiones · "
                  "solo recepción pasiva + web/QRZ")
        else:
            print(f"🔇 Países sin mensaje: {globals().get('PAISES_SIN_MENSAJE', [])}")
            print(f"🤫 Cortesía RF: 1 intento · tope "
                  f"{globals().get('MENSAJES_MAX_DIA', 120)} msg/día")
        print(f"📊 Tarjetas ya emitidas hoy: {self.eqsl_hoy} (recuperadas del JSON)")
        print("=" * 60)

        if GITHUB_TOKEN:
            self.publicador.probar_conexion()
            self._publicar_club()
        # 🛡️ v4.4: dedupe único del ADIF completo al arranque
        try:
            adif_guard.dedupe_archivo(self.adif.ruta_completo)
        except Exception as e:
            print(f"⚠️ ADIF GUARD arranque: {e}")
        if not globals().get("MODO_SWL_PURO", False):
            self.mensajes.iniciar()
        threading.Thread(target=self._bucle_resumen, daemon=True).start()
        threading.Thread(target=self._bucle_reintentos, daemon=True).start()
        threading.Thread(target=self._bucle_beacon, daemon=True).start()
        threading.Thread(target=self._bucle_watchdog, daemon=True).start()
        threading.Thread(target=self._bucle_latido, daemon=True).start()
        self.telegram.enviar(f"🤖 Bot APRS {CALLSIGN} v4.9 (1 QSO/mes + evento dual blindado) iniciado.")

        hosts = []
        for h in [SERVIDOR, "noam.aprs2.net", "euro.aprs2.net", "rotate.aprs2.net"]:
            if h not in hosts:
                hosts.append(h)

        # 🩹 v4.6: lógica RX probada de v4.3 (passcode real desde el inicio)
        self._login_fallos = 0
        self._solo_lectura = False

        while True:
            host = hosts[self._rx_host_idx % len(hosts)]
            print(f"⏳ {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC · "
                  f"intentando RX via {host}"
                  f"{' (SOLO LECTURA)' if self._solo_lectura else ''}...")
            try:
                pwd = -1 if self._solo_lectura else passcode(CALLSIGN)
                conexion = aprslib.IS(CALLSIGN, passwd=pwd,
                                      host=host, port=PUERTO)
                conexion.set_filter(self.construir_filtro())
                conexion.connect()
                self.rx_conn = conexion
                self._rx_fallos = 0
                self._login_fallos = 0
                self._rx_up = time.time()
                print(f"📡 RX conectado via {host}"
                      f"{' (solo lectura)' if self._solo_lectura else ''}")
                self._bucle_rx(conexion)
            except KeyboardInterrupt:
                print("\n👋 Bot detenido. ¡73s!")
                break
            except Exception as e:
                self.rx_conn = None
                self._rx_fallos += 1
                msg = str(e).lower()
                # 🩹 v4.6: "password" también cuenta como error de login
                es_login = ("login" in msg) or ("password" in msg)
                if es_login:
                    self._login_fallos += 1
                    self._rx_quick += 1
                    if self._login_fallos >= 3 and not self._solo_lectura:
                        self._solo_lectura = True
                        print("🔐 Login rechazado 3 veces → "
                              "pasando a RX SOLO LECTURA (pass -1)")
                else:
                    if time.time() - self._rx_up < 60:
                        self._rx_quick += 1
                    else:
                        self._rx_quick = 0
                if self._rx_quick >= 2:
                    self._rx_host_idx += 1
                    self._rx_quick = 0
                    print(f"🔀 RX inestable: cambiando a "
                          f"{hosts[self._rx_host_idx % len(hosts)]}")
                if es_login:
                    espera = 60
                else:
                    espera = min(5 * (2 ** min(self._rx_fallos - 1, 6)), 300)
                if self._rx_fallos >= 6:
                    print("🧊 Muchos fallos seguidos: posible throttle o "
                          "bloqueo temporal — paciencia...")
                print(f"⚠️ Conexión perdida: {e} — reintentando en {espera} s...")
                try:
                    time.sleep(espera)
                except KeyboardInterrupt:
                    print("\n👋 Bot detenido. ¡73s!")
                    break

if __name__ == "__main__":
    BotAPRS().iniciar()