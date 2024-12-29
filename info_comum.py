# Este ficheiro contém parâmetros que podem ser acedidos por qualquer agente no
# sistema e incluem JIDs, endereço do servidor XMPP e outros parâmetros globais

# Servidor
SERVERS = ["192.168.35.1", "desktop-j59unhi"]
XMPP_SERVER = SERVERS[1] # Placeholder para o endereço do servidor XMPP
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
ESPECIALIDADES = [
    "Cardiologia", "Cirurgia Geral", "Gastrenterologia", "Medicina Interna"
    "Ortopedia", "Cirurgia Cardiotorácica", "Cuidados Gerais"
]
TURNOS = ["turno1", "turno2", "turno3"]

# Valores de referência
BPM_BAIXO_IDEAL = 60
BPM_CIMA_IDEAL = 100
TEMP_IDEAL = 37
BF_IDEAL = 20

# Limites iniciais para gerar valores
BPM_BAIXO_INICIAL = 40
BPM_CIMA_INICIAL = 220
BF_BAIXO_INICIAL = 6
BF_CIMA_INICIAL = 34
TEMP_BAIXO_INICIAL = 30
TEMP_CIMA_INICIAL = 44
