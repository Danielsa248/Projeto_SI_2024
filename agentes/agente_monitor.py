from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

import jsonpickle as jp

try:
    from info_comum import *
    from classes.status_paciente import *
except ImportError:
    from Projeto_SI_2024.info_comum import *
    from Projeto_SI_2024.classes.status_paciente import *


# Classe representativa do Agente Monitor
class AgenteMonitor(Agent):
    # Mapa para monitorização do estado dos pacientes {jid : StatusPaciente}
    pacientes = dict()

    async def setup(self):
        print(f"AGENTE MONITOR: A iniciar...")
        monitorizar_pacientes = self.MonitorizarPacientes()
        self.add_behaviour(monitorizar_pacientes)


    '''
    Função auxiliar utilizada para determinar o grau de prioridade
    de um paciente com base nos dados enviados pelo mesmo.
    '''
    def determinar_grau(self, dados_paciente):
        bpm = dados_paciente.get_bpm()
        temp = dados_paciente.get_temp()
        bf = dados_paciente.get_bf()

        if TEMP_BAIXO_IDEAL <= temp <= TEMP_CIMA_IDEAL:
            grau_temp = GRAU_MIN
        elif temp < TEMP_BAIXO_IDEAL:
            dif = abs(TEMP_BAIXO_IDEAL - temp)
            dif_escalada = min(dif, TEMP_CIMA_INICIAL - TEMP_CIMA_IDEAL)
            grau_temp = GRAU_MIN + 1 + (dif_escalada / (TEMP_CIMA_INICIAL - TEMP_CIMA_IDEAL)) * (GRAU_MAX - GRAU_MIN - 1)
        else:
            dif = abs(TEMP_CIMA_IDEAL - temp)
            dif_escalada = min(dif, TEMP_BAIXO_IDEAL - TEMP_BAIXO_INICIAL)
            grau_temp = GRAU_MIN + 1 + (dif_escalada / (TEMP_BAIXO_IDEAL - TEMP_BAIXO_INICIAL)) * (GRAU_MAX - GRAU_MIN - 1)

        if BF_BAIXO_IDEAL <= bf <= BF_CIMA_IDEAL:
            grau_bf = GRAU_MIN
        elif bf < BF_BAIXO_IDEAL:
            dif = abs(BF_BAIXO_IDEAL - bf)
            dif_escalada = min(dif, BF_CIMA_INICIAL - BF_CIMA_IDEAL)
            grau_bf = GRAU_MIN + 1 + (dif_escalada / (BF_CIMA_INICIAL - BF_CIMA_IDEAL)) * (GRAU_MAX - GRAU_MIN - 1)
        else:
            dif = abs(BF_CIMA_IDEAL - bf)
            dif_escalada = min(dif, BF_BAIXO_IDEAL - BF_BAIXO_INICIAL)
            grau_bf = GRAU_MIN + 1 + (dif_escalada / (BF_BAIXO_IDEAL - BF_BAIXO_INICIAL)) * (GRAU_MAX - GRAU_MIN - 1)

        if BPM_BAIXO_IDEAL <= bpm <= BPM_CIMA_IDEAL:
            grau_bpm = GRAU_MIN
        elif bpm < BPM_BAIXO_IDEAL:
            dif = abs(BPM_BAIXO_IDEAL - bpm)
            dif_escalada = min(dif, BPM_CIMA_INICIAL - BPM_CIMA_IDEAL)
            grau_bpm = GRAU_MIN + 1 + (dif_escalada / (BPM_CIMA_INICIAL - BPM_CIMA_IDEAL)) * (GRAU_MAX - GRAU_MIN - 1)
        else:
            dif = abs(BPM_CIMA_IDEAL - bpm)
            dif_escalada = min(dif, BPM_BAIXO_IDEAL - BPM_BAIXO_INICIAL)
            grau_bpm = GRAU_MIN + 1 + (dif_escalada / (BPM_BAIXO_IDEAL - BPM_BAIXO_INICIAL)) * (GRAU_MAX - GRAU_MIN - 1)

        return round((grau_temp + grau_bf + grau_bpm) / 3)


    '''
    Comportamento referente à monitorização constante dos Agentes Paciente, comunicando
    com o Agente Alerta quando o grau de prioridade determinado é elevado o suficiente.
    
    NOTA: Este comportamento é também responsável pelo envio de atualizações ao
    Agente Unidade e descarta pacientes quando o grau de prioridade determinado
    é igual ou menor ao valor mínimo definido para esse parâmetro (GRAU_MIN) ou
    quando recebe dados não-graves N vezes seguidas (N = LIMITE_CONTADOR).
    '''
    class MonitorizarPacientes(CyclicBehaviour):
        async def run(self):
            dados = await self.receive()
            if (dados and (dados.get_metadata("performative") == "inform") and
                (dados.get_metadata("ontology") == "dados_paciente")):
                # Processamento dos dados recebidos
                dados_paciente = jp.decode(dados.body)
                paciente_jid = dados_paciente.get_jid()
                grau = self.agent.determinar_grau(dados_paciente)
                print(f"AGENTE MONITOR: Os dados de {extrair_nome_agente(paciente_jid)} têm gravidade de grau {grau}.")
                dados_paciente.set_grau(grau)

                if paciente_jid in self.agent.pacientes.keys():
                    self.agent.pacientes[paciente_jid].set_grau(grau)
                    self.agent.pacientes[paciente_jid].set_contador(self.agent.pacientes[paciente_jid].get_contador() + 1)

                else:
                    self.agent.pacientes[paciente_jid] = StatusPaciente(paciente_jid, grau, 1)

                status_atual = self.agent.pacientes[paciente_jid]
                # Processamento da resposta com base no estado do paciente
                if grau >= LIMITE_ALERTA:
                    print(f"AGENTE MONITOR: Os dados de {extrair_nome_agente(paciente_jid)} serão reencaminhados para o Agente Alerta.")
                    alerta = Message(to=AGENTE_ALERTA)
                    alerta.set_metadata("performative", "inform")
                    alerta.set_metadata("ontology", "alerta")
                    alerta.body = jp.encode(dados_paciente)
                    self.agent.pacientes[paciente_jid].set_contador(1)
                    await self.send(alerta)

                elif (grau <= GRAU_MIN) or (status_atual.get_contador() >= LIMITE_CONTADOR):
                    print(f"AGENTE MONITOR: O {extrair_nome_agente(paciente_jid)} vai deixar de ser monitorizado.")
                    self.agent.pacientes.pop(paciente_jid)
                    dados_paciente.set_grau(GRAU_MIN) # NOTA: O grau é posto a 0 para a comunicação com o Agente Unidade
                    resposta_paciente = Message(to=paciente_jid)
                    resposta_paciente.set_metadata("performative", "refuse")
                    resposta_paciente.set_metadata("ontology", "stop_dados")
                    await self.send(resposta_paciente)

                else:
                    print(f"AGENTE MONITOR: O {extrair_nome_agente(paciente_jid)} continuará a ser monitorizado.")
                    resposta_paciente = Message(to=paciente_jid)
                    resposta_paciente.set_metadata("performative", "refuse")
                    resposta_paciente.set_metadata("ontology", "novos_dados")
                    await self.send(resposta_paciente)

                # Sincronização com o Agente Unidade
                atualizacao = Message(to=AGENTE_UNIDADE)
                atualizacao.set_metadata("performative", "inform")
                atualizacao.body = jp.encode(dados_paciente)
                await self.send(atualizacao)
