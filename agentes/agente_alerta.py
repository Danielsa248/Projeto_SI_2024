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
        atualizar_pacientes = self.AtualizarPacientes()
        self.add_behaviour(processar_alertas)
        self.add_behaviour(aguardar_resposta)
        self.add_behaviour(tratar_filas_de_espera)
        self.add_behaviour(atualizar_pacientes)


    # Função auxiliar para construção das mensagens a enviar ao Agente Gestor de Médicos
    def mensagem_gestor_medicos(self, dados_paciente):
        requisicao = Message(to=AGENTE_GESTOR_MEDICOS)
        requisicao.set_metadata("performative", "request")
        requisicao.body = jp.encode(dados_paciente)
        return requisicao


    '''
    Comportamento referente à espera de alertas enviados pelo Agente Monitor
    e envio dos mesmos para o Agente Gestor de Médicos. A resposta às mensagens
    enviadas neste comportamento é realizada ao nível do comportamento AguardarResposta.
    '''
    class ProcessarAlertas(CyclicBehaviour):
        async def run(self):
            alerta = await self.receive()
            if alerta and (alerta.get_metadata("performative") == "inform") and (alerta.get_metadata("ontology") == "alerta"):
                dados_paciente = jp.decode(alerta.body)
                paciente_jid = dados_paciente.get_jid()
                print(f"AGENTE ALERTA: Recebido alerta relativo ao {extrair_nome_agente(paciente_jid)}.")

                await self.send(self.agent.mensagem_gestor_medicos(dados_paciente))
                print(f"AGENTE ALERTA: Enviada requisição para o tratamento do {extrair_nome_agente(paciente_jid)}.")


    '''
    Comportamento referente ao processamento de respostas aos pedidos de
    tratamento enviadas pelo Agente Gestor de Médicos. Os dados dos pacientes
    são adicionados ou removidos a filas de espera conforme a resposta obtida.
    '''
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
    para pacientes nas filas de espera. A resposta às mensagens enviadas neste
    comportamento é realizada ao nível do comportamento AguardarResposta.
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


    '''
    Comportamento referente à receção de atualizações nas especialidades
    em que um paciente está internado e atualização dos dados do mesmo
    na respetiva fila de espera (Se os dados ainda lá estiverem)
    '''
    class AtualizarPacientes(CyclicBehaviour):
        async def run(self):
            update = await self.receive(timeout=10)
            if update and update.get_metadata("performative") == "inform" and update.get_metadata("ontology") == "update_especialidade":
                fila = LIMITE_ALERTA
                encontrado = False
                async with self.agent.lock:
                    while fila <= GRAU_MAX and not encontrado:
                        for dados_paciente in self.agent.filas_de_espera[fila]:
                            paciente_jid = dados_paciente.get_jid()
                            if paciente_jid == update.sender:
                                dados_paciente.set_especialidade(update.body)
                                print(f"AGENTE ALERTA: O {extrair_nome_agente(paciente_jid)} trocou de especialidade.")
                                encontrado = True
                                break
                        fila += 1
