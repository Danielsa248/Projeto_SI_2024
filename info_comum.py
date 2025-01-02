# Este ficheiro contém parâmetros que podem ser acedidos por qualquer agente no
# sistema e incluem JIDs, endereço do servidor XMPP e outros parâmetros globais

# Servidor
SERVERS = ["192.168.35.1", "desktop-j59unhi"]
XMPP_SERVER = SERVERS[1]
PASSWORD = "NOPASSWORD"

# JIDs
AGENTE_UNIDADE = f"Unidade@{XMPP_SERVER}"
AGENTE_MONITOR = f"Monitor@{XMPP_SERVER}"
AGENTE_ALERTA = f"Alerta@{XMPP_SERVER}"
AGENTE_GESTOR_MEDICOS = f"GestorMedicos@{XMPP_SERVER}"

# Constantes globais
GRAU_MIN = 0
GRAU_MAX = 9
LIMITE_ALERTA = 5
LIMITE_CONTADOR = 5
COOLDOWN_MAX_ALERTA = 2000000#200
ESPECIALIDADES = [
    "Cardiologia", "Cirurgia Geral", "Gastrenterologia", "Medicina Interna"
    "Ortopedia", "Cirurgia Cardiotorácica", "Cuidados Gerais"
]
TURNOS = ["turno1", "turno2"]

# Valores de referência ideais
BPM_BAIXO_IDEAL = 60
BPM_CIMA_IDEAL = 100
TEMP_BAIXO_IDEAL = 36.1
TEMP_CIMA_IDEAL = 37.2
BF_BAIXO_IDEAL = 12
BF_CIMA_IDEAL = 25

# Limites iniciais para gerar valores
BPM_BAIXO_INICIAL = 40
BPM_CIMA_INICIAL = 220
BF_BAIXO_INICIAL = 6
BF_CIMA_INICIAL = 34
TEMP_BAIXO_INICIAL = 30
TEMP_CIMA_INICIAL = 44

# Fator de incrementação
K = 0.2

# Funções globais
def extrair_nome_agente(agente_jid):
    return str(agente_jid).split("@")[0].upper()
