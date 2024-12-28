# Este ficheiro contém parâmetros que podem ser acedidos por qualquer agente no
# sistema e incluem JIDs, endereço do servidor XMPP e outros parâmetros globais

# Servidor
XMPP_SERVER = "192.168.35.1" # Placeholder para o endereço do servidor XMPP
PASSWORD = "NOPASSWORD"

# JIDs
AGENTE_UNIDADE = f"AgenteUnidade@{XMPP_SERVER}" # Substituir pelo JID do Agente Unidade
AGENTE_MONITOR = f"AgenteMonitor@{XMPP_SERVER}" # Substituir pelo JID do Agente Monitor
AGENTE_ALERTA = f"AgenteAlerta@{XMPP_SERVER}" # Substituir pelo JID do Agente Alerta
AGENTE_GESTOR_MEDICOS = f"AgenteGestorMedicos@{XMPP_SERVER}" # Substituir pelo JID do Gestor de Médicos
AGENTE_PACIENTE = f"AgentePaciente@{XMPP_SERVER}" # Substituir pelo JID do Agente Paciente

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
bpmbaixo_ideal = 60
bpmcima_ideal = 100
temperatura_ideal = 37
bf_ideal = 20
# Valores iniciais
bpmbaixoinicial = 40
bpmcimainicial = 220
bfbaixoinicial = 6
bfcimainicial = 34
tempbaixoinicial = 30
tempcimainicial = 44
