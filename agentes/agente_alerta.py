from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message

import asyncio
import jsonpickle as jp

try:
    from info_comum import *
    from classes.dados_paciente import *
except ImportError:
    from Projeto_SI_2024.info_comum import *
    from Projeto_SI_2024.classes.dados_paciente import *


# Classe representativa do Agente Alerta
class AgenteAlerta(Agent):
    # Filas de espera para re-tentativa de envio de alertas
    filas_de_espera = {grau: [] for grau in range(LIMITE_ALERTA, GRAU_MAX + 1)}

    # Lock para bloqueio de acessos simultâneos a uma lista por dois behaviours
    lock = asyncio.Lock()

    async def setup(self):
        print(f"AGENTE ALERTA: A iniciar...")
        processar_alertas = self.ProcessarAlertas()
        aguardar_resposta = self.AguardarResposta()
        tratar_filas_de_espera = self.TratarFilasDeEspera(period=10)
        self.add_behaviour(processar_alertas)
        self.add_behaviour(aguardar_resposta)
        self.add_behaviour(tratar_filas_de_espera)


    # Função auxiliar para construção das mensagens a enviar ao Agente Gestor de Médicos
    @staticmethod
    def mensagem_gestor_medicos(dados_paciente):
        requisicao = Message(to=AGENTE_GESTOR_MEDICOS)
        requisicao.set_metadata("performative", "request")
        requisicao.body = jp.encode(dados_paciente)
        return requisicao


    '''
    Comportamento referente à espera de alertas enviados pelo Agente Monitor
    e envio dos mesmos para o Agente Gestor de Médicos. Caso não hajam médicos
    disponíveis para realizar o tratamento, o paciente é posicionado numa fila
    de espera conforme o seu grau de prioridade.
    '''
    class ProcessarAlertas(CyclicBehaviour):
        async def run(self):
            alerta = await self.receive()
            if alerta and (alerta.get_metadata("performative") == "inform"):
                dados_paciente = jp.decode(alerta.body)
                paciente_jid = dados_paciente.get_jid()
                print(f"AGENTE ALERTA: Recebido alerta relativo ao {extrair_nome_agente(paciente_jid)}.")

                await self.send(self.agent.mensagem_gestor_medicos(dados_paciente))
                print(f"AGENTE ALERTA: Enviada requisição para o tratamento do {extrair_nome_agente(paciente_jid)}.")


    class AguardarResposta(CyclicBehaviour):
        async def run(self):
            resposta = await self.receive()
            if resposta and (resposta.get_metadata("performative") == "confirm"):
                dados_paciente = jp.decode(resposta.body)
                paciente_jid = dados_paciente.get_jid()
                grau = dados_paciente.get_grau()
                if dados_paciente in self.agent.filas_de_espera[grau]:
                    async with self.agent.lock:
                        self.agent.filas_de_espera[grau].remove(dados_paciente)
                        print(f"AGENTE ALERTA: O {extrair_nome_agente(paciente_jid)} abandonou a fila de espera de grau {grau}.")
                else:
                    print(f"AGENTE ALERTA: Confirmado o tratamento do {extrair_nome_agente(paciente_jid)}.")

            elif resposta and (resposta.get_metadata("performative") == "refuse"):
                dados_paciente = jp.decode(resposta.body)
                paciente_jid = dados_paciente.get_jid()
                grau = dados_paciente.get_grau()
                if dados_paciente in self.agent.filas_de_espera[grau]:
                    print(f"AGENTE ALERTA: O {extrair_nome_agente(paciente_jid)} continuará na fila de espera de grau {grau}.")
                else:
                    async with self.agent.lock:
                        self.agent.filas_de_espera[grau].append(dados_paciente)
                        print(f"AGENTE ALERTA: O {extrair_nome_agente(paciente_jid)} foi colocado na fila de espera {grau}.")


    '''
    Comportamento referente ao envio periódico de requisições de tratamento
    para pacientes nas filas de espera. Caso as requisições sejam
    cumpridas o paciente abandona a fila de espera em que se encontra.
    '''
    class TratarFilasDeEspera(PeriodicBehaviour):
        async def run(self):
            fila = GRAU_MAX
            async with self.agent.lock:
                while fila >= LIMITE_ALERTA:
                    for dados_paciente in self.agent.filas_de_espera[fila][:]:
                        paciente_jid = dados_paciente.get_jid()

                        await self.send(self.agent.mensagem_gestor_medicos(dados_paciente))
                        print(f"AGENTE ALERTA: Enviada **NOVA** requisição para o tratamento do {extrair_nome_agente(paciente_jid)}.")

                    fila -= 1
