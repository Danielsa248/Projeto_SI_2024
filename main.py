from agentes.agente_paciente import *
from agentes.agente_unidade import *
from agentes.agente_monitor import *
from agentes.agente_alerta import *
from agentes.agente_gestor_medicos import *
from agentes.agente_medico import *
from info_comum import *

from spade import quit_spade

import time


def main():
    futures = []

    unidade = AgenteUnidade(AGENTE_UNIDADE, PASSWORD)
    future = unidade.start(auto_register=True)
    futures.append(future)

    monitor = AgenteMonitor(AGENTE_MONITOR, PASSWORD)
    future = monitor.start(auto_register=True)
    futures.append(future)

    alerta = AgenteAlerta(AGENTE_ALERTA, PASSWORD)
    future = alerta.start(auto_register=True)
    futures.append(future)

    gestor_medicos = AgenteGestorMedicos(AGENTE_GESTOR_MEDICOS, PASSWORD)
    future = gestor_medicos.start(auto_register=True)
    futures.append(future)

    for future in futures:
        future.result()

    futures = []

    medicos = []
    num_medicos = 0
    while num_medicos < 3:
        medico = AgenteMedico(f"Medico{num_medicos}@{XMPP_SERVER}", PASSWORD)
        future = medico.start(auto_register=True)
        futures.append(future)
        medicos.append(medico)
        num_medicos += 1
    for future in futures:
        future.result()

    futures = []

    pacientes = []
    num_pacientes = 0
    while num_pacientes < 10:
        paciente = AgentePaciente(f"Paciente{num_pacientes}@{XMPP_SERVER}", PASSWORD)
        future = paciente.start(auto_register=True)
        futures.append(future)
        pacientes.append(paciente)
        num_pacientes += 1
    for future in futures:
        future.result()

    while unidade.is_alive() and monitor.is_alive() and alerta.is_alive() and gestor_medicos.is_alive():
        try:
            '''
            # A cada 3 segundos cria um paciente
            for _ in range(10):
                paciente = Paciente(f"Paciente{num_pacientes}@{XMPP_SERVER}", PASSWORD)
                future = paciente.start(auto_register=True)
                future.result()
                pacientes.append(paciente)
                num_pacientes += 1
            '''
            time.sleep(1)

        except KeyboardInterrupt:
            print("Encerrando agentes...")
            for paciente in pacientes:
                paciente.stop()
            for medico in medicos:
                medico.stop()
            unidade.stop()
            monitor.stop()
            alerta.stop()
            gestor_medicos.stop()
            break

if __name__ == "__main__":
    try:
        main()
    finally:
        quit_spade()
