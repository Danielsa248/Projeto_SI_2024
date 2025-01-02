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
                    self.agent.filas_de_espera[grau].append((dados_paciente, COOLDOWN_MAX_ALERTA)) # (dados, cooldown)
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
                    for i, (dados_paciente, cooldown) in enumerate(self.agent.filas_de_espera[fila][:]):
                        # Envio dos dados para tentativa de tratamento
                        if cooldown > COOLDOWN_MAX_ALERTA:
                            paciente_jid = dados_paciente.get_jid()
                            print(f"AGENTE ALERTA: Será enviado o pedido de tratamento de {extrair_nome_agente(paciente_jid)}.")
                            # await asyncio.sleep(3)
                            requisicao = Message(to=AGENTE_GESTOR_MEDICOS)
                            requisicao.set_metadata("performative", "request")
                            requisicao.body = jp.encode(dados_paciente)
                            await self.send(requisicao)

                            # Processamento da resposta do Agente Gestor de Médicos
                            resposta = await self.receive(timeout=10)

                            if resposta and (resposta.get_metadata("performative") == "refuse"):
                                print(f"AGENTE ALERTA: O pedido de tratamento de {extrair_nome_agente(paciente_jid)} irá regressar à fila de espera.")
                                # await asyncio.sleep(3)
                                self.agent.filas_de_espera[fila][i] = (dados_paciente, 1) # Reínicia o contador

                            elif resposta and (resposta.get_metadata("performative") == "confirm"):
                                print(f"AGENTE ALERTA: O pedido de tratamento de {extrair_nome_agente(paciente_jid)} será cumprido.")
                                # await asyncio.sleep(3)
                                if i in self.agent.filas_de_espera[fila]:
                                    self.agent.filas_de_espera[fila].remove(i) # Remove paciente tratado da fila de espera
                                    serviu_requisicao = True
                                    break # Regressa ao inicío da fila de maior prioridade quando serve um pedido

                        else:
                            self.agent.filas_de_espera[fila][i] = (dados_paciente, cooldown + 1)

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
                for fila in range(GRAU_MAX - 1, LIMITE_ALERTA - 1, -1):
                    for j, (dados_paciente, cooldown) in enumerate(self.agent.filas_de_espera[fila][:]):
                        self.agent.filas_de_espera[fila + 1].append((dados_paciente, cooldown))
                        if j in self.agent.filas_de_espera[fila]:
                            self.agent.filas_de_espera[fila].remove(j)
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
