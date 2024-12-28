# Este ficheiro contém parâmetros que podem ser acedidos por qualquer agente no
# sistema e incluem JIDs, endereço do servidor XMPP e outros parâmetros globais

# Servidor
XMPP_SERVER = "desktop-j59unhi" #"192.168.35.1" # Placeholder para o endereço do servidor XMPP
PASSWORD = "NOPASSWORD"

# JIDs
AGENTE_UNIDADE = f"AgenteUnidade@{XMPP_SERVER}" # Substituir pelo JID do Agente Unidade
AGENTE_MONITOR = f"AgenteMonitor@{XMPP_SERVER}" # Substituir pelo JID do Agente Monitor
AGENTE_ALERTA = f"AgenteAlerta@{XMPP_SERVER}" # Substituir pelo JID do Agente Alerta
AGENTE_GESTOR_MEDICOS = f"AgenteGestorMedicos@{XMPP_SERVER}" # Substituir pelo JID do Gestor de Médicos

# Constantes globais
GRAU_MIN = 0
GRAU_MAX = 9
LIMITE_ALERTA = 5
ESPECIALIDADES = [
    "Cardiologia", "Cirurgia Geral", "Gastrenterologia", "Medicina Interna"
    "Ortopedia", "Cirurgia Cardiotorácica", "Cuidados Geral"
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


