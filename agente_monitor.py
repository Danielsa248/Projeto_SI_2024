from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

import jsonpickle as jp

from info_comum import *


# Classe representativa do Agente Monitor
class AgenteMonitor(Agent):
    # Mapa para monitorização do estado dos pacientes {jid : grau}
    pacientes = dict()

    async def setup(self):
        print(f"{self.jid}: A iniciar...")
        monitorizar_pacientes = self.MonitorizarPacientes()
        feedback_alerta = self.FeedbackAlerta()
        self.add_behaviour(monitorizar_pacientes)
        self.add_behaviour(feedback_alerta)

    def determinar_grau(self, dados_paciente):
        bpm = dados_paciente.get_bpm()
        temp = dados_paciente.get_temp()
        bf = dados_paciente.get_bf()

        grau_temp = GRAU_MAX - abs(temp - TEMP_IDEAL) / (TEMP_CIMA_INICIAL - TEMP_IDEAL) * (GRAU_MAX - GRAU_MIN)
        grau_bf =  GRAU_MAX - abs(bf- BF_IDEAL) / (BF_CIMA_INICIAL - BF_IDEAL) * (GRAU_MAX - GRAU_MIN)
        grau_bpm = GRAU_MAX // 2

        if BPM_BAIXO_IDEAL <= bpm <= BPM_CIMA_IDEAL:
            grau_bpm = GRAU_MIN

        elif bpm < BPM_BAIXO_IDEAL:
            grau_bpm = GRAU_MAX - (bpm - BPM_BAIXO_INICIAL) / (BPM_BAIXO_IDEAL - BPM_BAIXO_INICIAL) * (GRAU_MAX - GRAU_MIN)

        else:
            grau_bpm = GRAU_MAX - (BPM_CIMA_INICIAL - bpm) / (BPM_CIMA_INICIAL - BPM_CIMA_IDEAL) * (GRAU_MAX - GRAU_MIN)

        return round((grau_temp + grau_bf + grau_bpm) / 3)


    '''
    Comportamento referente à monitorização constante dos Agentes Paciente, comunicando
    com o Agente Alerta quando o grau de prioridade determinado é elevado o suficiente.
    
    NOTA: Este comportamento é também responsável pelo envio de atualizações ao
    Agente Unidade e descarta pacientes quando o grau de prioridade determinado
    é igual ou menor ao valor mínimo definido para esse parâmetro (GRAU_MIN).
    '''
    class MonitorizarPacientes(CyclicBehaviour):
        async def on_start(self):
            print(f"{self.agent.jid}: Pronto para monitorizar pacientes.")

        async def run(self):
            dados = await self.receive()
            if (dados and (dados.get_metadata("performative") == "inform") and
                (dados.get_metadata("ontology") == "dados_paciente")):
                # Processamento dos dados recebidos
                dados_paciente = jp.decode(dados.body)
                paciente_jid = dados_paciente.get_jid()
                grau = self.agent.determinar_grau(dados_paciente)
                dados_paciente.set_grau(grau)
                self.agent.pacientes[paciente_jid] = grau

                # Interpretação dos dados recebidos
                if grau <= GRAU_MIN:
                    self.agent.pacientes.pop(paciente_jid, None) # Para de monitorizar o paciente
                elif grau >= LIMITE_ALERTA:
                    alerta = Message(to=AGENTE_ALERTA)
                    alerta.set_metadata("performative", "inform")
                    alerta.body = jp.encode(dados_paciente)
                    await self.send(alerta) # Remete os dados para o Agente Alerta

                # Sincronização com o Agente Unidade
                atualizacao = Message(to=AGENTE_UNIDADE)
                atualizacao.set_metadata("performative", "inform")
                atualizacao.body = jp.encode(dados_paciente)
                await self.send(atualizacao)

    '''
    Comportamento referente à receção de atualizações nos graus de prioridade
    de pacientes em espera no Agente Alerta, enviadas pelo próprio.
    
    NOTA: Este comportamento existe porque o Agente Alerta pode atualizar graus de
    prioridade de pacientes e o Agente Monitor deve manter-se a par dessas atualizações.
    '''
    class FeedbackAlerta(CyclicBehaviour):
        async def on_start(self):
            print(f"{self.agent.jid}: Pronto para receber feedback do Agente Alerta.")

        async def run(self):
            dados = await self.receive()
            if (dados and (dados.get_metadata("performative") == "inform") and
                (dados.get_metadata("ontology") == "atualizacao_grau")):
                # Processamento dos dados recebidos
                dados_paciente = jp.decode(dados.body)
                paciente_jid = dados_paciente.get_jid()
                grau = dados_paciente.get_grau()
                self.agent.pacientes[paciente_jid] = grau
