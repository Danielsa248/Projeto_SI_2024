from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message

import random
import jsonpickle

from classes.dados_paciente import *
from info_comum import *


class AgentePaciente(Agent):

    async def setup(self):
        print(f"{extrair_nome_agente(self.jid)}: A iniciar...")
        self.set("bpm", random.randint(BPM_BAIXO_INICIAL,BPM_CIMA_INICIAL))
        self.set("bf", random.randint(BF_BAIXO_INICIAL,BF_CIMA_INICIAL))
        self.set("temp", random.randint(TEMP_BAIXO_INICIAL,TEMP_CIMA_INICIAL))
        self.set("esp", random.choice(ESPECIALIDADES))

        self.registar_unidade = self.RegistarNaUnidade()
        self.esperar_tratamento = self.EsperarTratamento()
        libertar_cama = self.LibertarCama()
        self.add_behaviour(self.registar_unidade)
        self.add_behaviour(self.esperar_tratamento)
        self.add_behaviour(libertar_cama)


    # Efetua o registo no Agente Unidade
    class RegistarNaUnidade(OneShotBehaviour):
        async def run(self):
            msg1 = Message(to=AGENTE_UNIDADE)
            msg1.set_metadata("performative", "subscribe")
            msg1.body = jsonpickle.encode(DadosPaciente(str(self.agent.jid),self.agent.get("esp"),
                                                        None,None,None,random.randint(GRAU_MIN,GRAU_MAX + 1)))
            await self.send(msg1)
            print(f"{extrair_nome_agente(self.agent.jid)}: Registo enviado ao Agente Unidade.")

            reply = await self.receive(timeout=10)
            if reply and reply.get_metadata("performative") == "refuse":
                print(f"{extrair_nome_agente(self.agent.jid)}: Os dados não são graves o suficiente para entrar na UCI.")
                await self.agent.stop()

            elif reply and (reply.get_metadata("performative") == "confirm") and (reply.get_metadata("ontology") == "registado"):
                print(f"{extrair_nome_agente(self.agent.jid)}: Pronto para enviar dados.")
                dados = Message(to=AGENTE_MONITOR)
                dados.set_metadata("performative", "inform")
                dados.set_metadata("ontology", "dados_paciente")
                dados.body = jsonpickle.encode(
                    DadosPaciente(str(self.agent.jid), self.agent.get("esp"), self.agent.get("bpm"),
                                  self.agent.get("bf"), self.agent.get("temp"), None))
                await self.send(dados)


    '''
    Aguarda a resposta aos dados médicos que enviou e envia novos
    dados ou termina a execução conforme a resposta que recebe.
    '''
    class EsperarTratamento(CyclicBehaviour):
        async def on_start(self):
            await self.agent.registar_unidade.join()

        async def run(self):
            msg = await self.receive()
            if msg and (msg.get_metadata("performative") == "refuse") and (msg.get_metadata("ontology") == "stop_dados"):
                self.kill()

            if msg and (((msg.get_metadata("performative") == "confirm") and (msg.get_metadata("ontology") == "tratado"))\
                    or ((msg.get_metadata("performative") == "refuse") and (msg.get_metadata("ontology") == "novos_dados"))):
                bpm_min = BPM_BAIXO_INICIAL + (0.1 * (BPM_BAIXO_IDEAL - BPM_BAIXO_INICIAL))
                bpm_max = BPM_CIMA_INICIAL - (0.2 * (BPM_CIMA_INICIAL - BPM_CIMA_IDEAL))
                self.set("bpm", random.randint(bpm_min, bpm_max))

                bf_min = BF_BAIXO_INICIAL + 1
                bf_max = BF_CIMA_INICIAL - 1
                temp_min = TEMP_BAIXO_INICIAL + 1
                temp_max = TEMP_CIMA_INICIAL - 1
                self.set("temp", random.randint(temp_min, temp_max))

                self.set("bf", random.randint(bf_min, bf_max))

                dados = Message(to=AGENTE_MONITOR)
                dados.set_metadata("performative", "inform")
                dados.set_metadata("ontology", "dados_paciente")
                dados.body = jsonpickle.encode(
                    DadosPaciente(str(self.agent.jid), self.agent.get("esp"), self.agent.get("bpm"),
                                  self.agent.get("bf"), self.agent.get("temp"), None))
                await self.send(dados)

            elif msg and (msg.get_metadata("performative") == "refuse") and (msg.get_metadata("ontology") == "novos_dados"):
                dados = Message(to=AGENTE_MONITOR)
                dados.set_metadata("performative", "inform")
                dados.set_metadata("ontology", "dados_paciente")
                dados.body = jsonpickle.encode(
                    DadosPaciente(str(self.agent.jid), self.agent.get("esp"), self.agent.get("bpm"),
                                  self.agent.get("bf"), self.agent.get("temp"), None))
                await self.send(dados)



    # Termina a execução quando o Agente Unidade confirma a saída do paciente da UCI
    class LibertarCama(CyclicBehaviour):
        async def on_start(self):
            await self.agent.esperar_tratamento.join()

        async def run(self):
            msg = await self.receive(timeout=10)
            if msg and (msg.get_metadata("performative") == "unsubscribe"):
                print(f"{extrair_nome_agente(self.agent.jid)}: ESTOU CURADO!!!!!!!!!!!!!!!!!!")
                await self.agent.stop()