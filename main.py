from agente_paciente import *
from agente_unidade import *
from agente_monitor import *
from agente_alerta import *
from agente_gestor_medicos import *
from agente_medico import *
from info_comum import *
import time
from spade import quit_spade


if __name__ == "__main__":
    unidade = AgenteUnidade(AGENTE_UNIDADE, PASSWORD)
    future = unidade.start(auto_register=True)
    future.result()

    monitor = AgenteMonitor(AGENTE_MONITOR, PASSWORD)
    future = monitor.start(auto_register=True)
    future.result()

    alerta = AgenteAlerta(AGENTE_ALERTA, PASSWORD)
    future = alerta.start(auto_register=True)
    future.result()

    gestor_medicos = AgenteGestorMedicos(AGENTE_GESTOR_MEDICOS, PASSWORD)
    future = gestor_medicos.start(auto_register=True)
    future.result()

    medicos = []
    num_medicos = 0
    while num_medicos < 5:
        medico = Medico(f"Medico{num_medicos}@{XMPP_SERVER}", PASSWORD)
        future = medico.start(auto_register=True)
        future.result()
        medicos.append(medico)
        num_medicos += 1

    pacientes = []
    num_pacientes = 0
    while num_pacientes < 3:
        paciente = Paciente(f"Paciente{num_pacientes}@{XMPP_SERVER}", PASSWORD)
        future = paciente.start(auto_register=True)
        future.result()
        pacientes.append(paciente)
        num_pacientes += 1

    while unidade.is_alive() and monitor.is_alive() and alerta.is_alive() and gestor_medicos.is_alive():
        try:
            # A cada 3 segundos cria um paciente
            for _ in range(10):
                paciente = Paciente(f"Paciente{num_pacientes}@{XMPP_SERVER}", PASSWORD)
                future = paciente.start(auto_register=True)
                future.result()
                pacientes.append(paciente)
                num_pacientes += 1
                time.sleep(3)

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

    quit_spade()