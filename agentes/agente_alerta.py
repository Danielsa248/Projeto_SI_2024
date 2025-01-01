from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message

import asyncio
import jsonpickle as jp

try:
    from info_comum import *
except ImportError:
    from Projeto_SI_2024.info_comum import *


# Classe representativa do Agente Alerta
class AgenteAlerta(Agent):
    # Filas de espera relativas a cada grau de prioridade
    filas_de_espera = {grau: [] for grau in range(LIMITE_ALERTA, GRAU_MAX + 1)}

    async def setup(self):
        print(f"AGENTE ALERTA: A iniciar...")
        esperar_alerta = self.EsperarAlertas()
        requisitar_tratamento = self.RequisitarTratamentos()
        reavaliar_prioridades = self.ReavaliarPrioridades(period=10)
        self.add_behaviour(esperar_alerta)
        self.add_behaviour(requisitar_tratamento)
        self.add_behaviour(reavaliar_prioridades)
        self.lock = asyncio.Lock()  # Usado para prevenir acessos simultâneos de
                                    # dois Behaviours à mesma lista de espera


    '''
    Comportamento referente à espera de alertas enviados pelo Agente Monitor e
    posicionamento dos mesmos em filas de espera conforme o seu grau de prioridade.

    NOTA: Este comportamento parte do princípio que este agente pode receber vários
    alertas em simultâneo e que pode ter de reenviar pedidos de tratamento em caso
    de rejeição dos mesmos pelo Agente Gestor de Médicos.
    '''
    class EsperarAlertas(CyclicBehaviour):
        async def run(self):
            alerta = await self.receive()
            async with self.agent.lock:
                if alerta and (alerta.get_metadata("performative") == "inform"):
                    dados_paciente = jp.decode(alerta.body)
                    paciente_jid = dados_paciente.get_jid()
                    grau = dados_paciente.get_grau()
                    self.agent.filas_de_espera[grau].append(dados_paciente)
                    print(f"AGENTE ALERTA: Recebido um alerta para o tratamento de {extrair_nome_agente(paciente_jid)}.")


    '''
    Comportamento referente ao envio de uma requisição de tratamento
    ao Agente Gestor de Médicos e tratamento da resposta recebida.

    NOTA: Este comportamento assume que os pedidos de tratamento estão organizados
    em diferentes filas de espera e tenta que sejam servidos de forma justa, promovendo
    o tratamento prioritário de pedidos mais urgentes, sem comprometer os restantes.
    '''
    class RequisitarTratamentos(CyclicBehaviour):
        async def run(self):
            async with self.agent.lock:
                fila = GRAU_MAX
                serviu_requisicao = False

                while (fila >= LIMITE_ALERTA) and not serviu_requisicao:
                    for dados_paciente in self.agent.filas_de_espera[fila][:]:
                        # Envio dos dados para tentativa de tratamento
                        paciente_jid = dados_paciente.get_jid()
                        print(f"AGENTE ALERTA: Será enviado o pedido de tratamento de {extrair_nome_agente(paciente_jid)}.")
                        # await asyncio.sleep(3) # Reduzir "spam" no terminal
                        self.agent.filas_de_espera[fila].remove(dados_paciente)
                        requisicao = Message(to=AGENTE_GESTOR_MEDICOS)
                        requisicao.set_metadata("performative", "request")
                        requisicao.body = jp.encode(dados_paciente)
                        await self.send(requisicao)

                        # Processamento da resposta do Agente Gestor de Médicos
                        resposta = await self.receive(timeout=5)
                        if resposta and (resposta.get_metadata("performative") == "refuse"):
                            print(f"AGENTE ALERTA: O pedido de tratamento de {extrair_nome_agente(paciente_jid)} irá regressar à fila de espera.")
                            # await asyncio.sleep(3) # Reduzir "spam" no terminal
                            nova_posicao = len(self.agent.filas_de_espera[fila]) // 2
                            self.agent.filas_de_espera[fila].insert(nova_posicao, dados_paciente) # "Puxa" o paciente de volta para o meio da fila
                        elif resposta and (resposta.get_metadata("performative") == "confirm"):
                            print(f"AGENTE ALERTA: O pedido de tratamento de {extrair_nome_agente(paciente_jid)} será cumprido.")
                            # await asyncio.sleep(3) # Reduzir "spam" no terminal
                            serviu_requisicao = True
                            break # Regressa ao inicío da fila de maior prioridade quando serve um pedido

                    fila -= 1


    '''
    Comportamento referente à atualização dos níveis de prioridade de
    pacientes cujos alertas gerados não tenham sido atendidos ao fim
    de X segundos, sendo trocada a fila de espera em que se encontram.
    
    NOTA: Este comportamento assume a existência de diferentes filas de espera, com
    diferentes prioridades. Para além disso, comunica as alterações nos graus de
    prioridade ao Agente Monitor e Agente Unidade, para efeitos de sincronização.
    '''
    class ReavaliarPrioridades(PeriodicBehaviour):
        async def run(self):
            async with self.agent.lock:
                for i in range(GRAU_MAX - 1, LIMITE_ALERTA - 1, -1):
                    for dados_paciente in self.agent.filas_de_espera[i][:]:
                        self.agent.filas_de_espera[i + 1].append(dados_paciente)
                        self.agent.filas_de_espera[i].remove(dados_paciente)
                        dados_paciente.set_grau(dados_paciente.get_grau() + 1)
                        print(f"AGENTE ALERTA: Subiu o grau de prioridade de {extrair_nome_agente(dados_paciente.get_jid())}.")

                        # Sincronização com o Agente Monitor
                        msg_monitor = Message(to=AGENTE_MONITOR)
                        msg_monitor.set_metadata("performative", "inform")
                        msg_monitor.set_metadata("ontology", "atualizacao_grau")
                        msg_monitor.body = jp.encode(dados_paciente)
                        await self.send(msg_monitor)

                        # Sincronização com o Agente Unidade
                        msg_unidade = Message(to=AGENTE_UNIDADE)
                        msg_unidade.set_metadata("performative", "inform")
                        msg_unidade.body = jp.encode(dados_paciente)
                        await self.send(msg_unidade)
