from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message

import jsonpickle as jp

from info_comum import *


# Classe representativa do Agente Alerta
class AgenteAlerta(Agent):
    # Estas filas de espera existem para balancear as prioridades de pedidos que chegam ao mesmo tempo
    filas_de_espera = {grau: [] for grau in range(LIMITE_ALERTA, GRAU_MAX + 1)}

    async def setup(self):
        print(f"{self.jid}: A iniciar...")
        esperar_alerta = self.EsperarAlertas()
        requisitar_tratamento = self.RequisitarTratamentos()
        reavaliar_prioridades = self.ReavaliarPrioridades(period=10)
        self.add_behaviour(esperar_alerta)
        self.add_behaviour(requisitar_tratamento)
        self.add_behaviour(reavaliar_prioridades)

    '''
    Comportamento referente à espera de alertas enviados
    pelo Agente Monitor e posicionamento dos mesmos em
    filas de espera conforme o grau de prioridade dos mesmos
    
    NOTA: Apenas faz sentido este comportamento existir
    se assumirmos que este agente pode receber vários alertas
    ao mesmo tempo e se tiver de reenviar pedidos de tratamento
    em caso de rejeição de pedidos pelo Agente Gestor de Médicos.
    '''
    class EsperarAlertas(CyclicBehaviour):
        async def on_start(self):
            print(f"{self.agent.jid}: Pronto para receber alertas.")

        async def run(self):
            alerta = await self.receive()
            if alerta and (alerta.get_metadata("performative") == "request"):
                dados_paciente = jp.decode(alerta.body)  # Decidir que dados receber aqui
                grau = dados_paciente.get_grau()
                self.agent.filas_de_espera[grau].append(dados_paciente)
                # Caso queiramos enviar confirmação ao Agente Monitor, fazê-lo aqui

    '''
    Comportamento referente ao envio de uma requisição de tratamento
    ao Agente Gestor de Médicos e tratamento da resposta recebida
    
    NOTA: Este comportamento parte do princípio que os pedidos de tratamento
    estão organizados em diferentes filas de prioridade e tenta que sejam
    servidos de forma justa. Se o comportamento anterior não for necessário,
    este comportamento tem de ser mudado.
    '''
    class RequisitarTratamentos(CyclicBehaviour):
        async def on_start(self):
            print(f"{self.agent.jid}: Pronto para requisitar tratamentos.")

        async def run(self):
            fila = GRAU_MAX
            serviu_requisicao = False

            while (fila >= LIMITE_ALERTA) and not serviu_requisicao:
                for dados_paciente in self.agent.filas_de_espera[fila][:]:
                    # Envio dos dados para tentativa de tratamento
                    requisicao = Message(to=AGENTE_GESTOR_MEDICOS)
                    requisicao.set_metadata("performative", "request")
                    requisicao.body = jp.encode(dados_paciente) # Decidir o que é que estes dados levam
                    await self.send(requisicao)

                    # Processamento da resposta do Agente Gestor de Médicos
                    resposta = await self.receive()
                    if resposta and (resposta.get_metadata("performative") == "refuse"):
                        nova_posicao = len(self.agent.filas_de_espera[fila]) // 2
                        self.agent.filas_de_espera[fila].remove(dados_paciente)
                        self.agent.filas_de_espera[fila].insert(nova_posicao,
                                                                dados_paciente) # "Puxa" o paciente de volta para o meio da fila
                    elif resposta and (resposta.get_metadata("performative") == "confirm"):
                        self.agent.filas_de_espera[fila].remove(dados_paciente)
                        serviu_requisicao = True
                        break # Regressa à fila de maior prioridade quando serve um pedido

                fila = fila - 1

    '''
    Comportamento referente à atualização dos níveis de prioridade
    de pacientes cujos alertas gerados não tenham sido atendidos ao
    fim de X segundos, sendo trocada a fila de espera em que se encontram
    
    NOTA: Só faz sentido este comportamento existir se houverem diferentes
    filas de espera com diferentes prioridades. De momento, este comportamento
    apenas comunica alterações nos graus de prioridade com o Agente Monitor e
    com o Agente Unidade. Isto poderá ser alterado.
    '''
    class ReavaliarPrioridades(PeriodicBehaviour):
        async def on_start(self):
            print(f"{self.agent.jid}: Pronto para reavaliar prioridades.")

        async def run(self):
            for i in range(GRAU_MAX - 1, LIMITE_ALERTA - 1, -1):
                for dados_paciente in self.agent.filas_de_espera[i][:]:
                    self.agent.filas_de_espera[i + 1].append(dados_paciente)
                    self.agent.filas_de_espera[i].remove(dados_paciente)
                    
                    msg_monitor = Message(to=AGENTE_MONITOR)
                    msg_monitor.set_metadata("performative", "inform")
                    msg_monitor.set_metadata("ontology", "atualizacao_grau")
                    msg_monitor.body = dados_paciente  # Mantém o Agente Monitor atualizado sobre os graus de prioridade
                    await self.send(msg_monitor)

                    msg_unidade = Message(to=AGENTE_UNIDADE)
                    msg_unidade.set_metadata("performative", "inform")
                    msg_unidade.body = dados_paciente  # Mantém o Agente Unidade atualizado sobre os graus de prioridade
                    await self.send(msg_unidade)
                    
                    # Vale a pena enviar atualização do grau de prioridade para o Paciente também?
