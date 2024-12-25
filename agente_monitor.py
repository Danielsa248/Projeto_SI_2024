from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

import jsonpickle as jp

from info_comum import *


# Classe representativa do Agente Monitor
class AgenteMonitor(Agent):
    # Mapa de monitorização do estado dos pacientes {jid : grau}
    pacientes = dict()

    async def setup(self):
        print(f"{self.jid}: A iniciar...")
        monitorizar_pacientes = self.MonitorizarPacientes()
        feedback_alerta = self.FeedbackAlerta()
        self.add_behaviour(monitorizar_pacientes)
        self.add_behaviour(feedback_alerta)

    '''
    Comportamento referente à monitorização constante dos Agentes Paciente,
    comunicando com o Agente Alerta quando o grau de prioridade determinado
    é elevado o suficiente, ou envio de rejeição ao Agente Paciente caso contrário.
    
    NOTA: Este comportamento é também responsável pelo envio de atualizações ao Agente Unidade
    e descarta pacientes quando o grau de prioridade determinado é igual a 0
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
                grau = self.agent.determinar_grau(dados_paciente) # Função ainda não criada
                dados_paciente.set_grau(grau)
                self.agent.pacientes[paciente_jid] = grau

                # Envio da resposta ao agente adequado e sincronização com o Agente Unidade
                if grau <= GRAU_MIN:
                    self.agent.pacientes.pop(paciente_jid, None) # Para de monitorizar um paciente quando o grau é 0
                elif grau >= LIMITE_ALERTA:
                    alerta = Message(to=AGENTE_ALERTA)
                    alerta.set_metadata("performative", "request")
                    alerta.body = dados_paciente # Remete os dados para o Agente Alerta
                    await self.send(alerta)
                else:
                    resposta = Message(to=dados_paciente.get_jid())
                    resposta.set_metadata("performative", "refuse") # Pode enviar só o refuse "seco"
                    resposta.body = dados_paciente # (OPCIONAL) Reenvia os dados para que o Paciente atualize o seu grau
                    await self.send(resposta)

                atualizacao = Message(to=AGENTE_UNIDADE)
                atualizacao.set_metadata("performative", "inform")
                atualizacao.body = dados_paciente # Mantém o Agente Unidade atualizado sobre os graus de prioridade
                await self.send(atualizacao)

    '''
    Comportamento referente à receção de atualizações nos graus de prioridade
    de pacientes que tenham sido enviados para o Agente Alerta e estão à espera
    de tratamento nas filas de espera do mesmo.
    
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
