from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message

import random
import jsonpickle

try:
    from info_comum import *
    from classes.dados_paciente import *
except ImportError:
    from Projeto_SI_2024.info_comum import *
    from Projeto_SI_2024.classes.dados_paciente import *


class AgentePaciente(Agent):

    async def setup(self):
        print(f"{extrair_nome_agente(self.jid)}: A iniciar...")
        self.set("bpm_max", random.randint((BPM_BAIXO_INICIAL + BPM_CIMA_INICIAL) // 2, BPM_CIMA_INICIAL + 1))
        self.set("bpm_min", random.randint(BPM_BAIXO_INICIAL, (BPM_CIMA_INICIAL + BPM_BAIXO_INICIAL) // 2))
        self.set("bf_max", random.randint((BF_BAIXO_INICIAL + BF_CIMA_INICIAL) // 2, BF_CIMA_INICIAL + 1))
        self.set("bf_min", random.randint(BF_BAIXO_INICIAL, (BF_CIMA_INICIAL + BF_BAIXO_INICIAL) // 2))
        self.set("temp_max", random.uniform((TEMP_BAIXO_INICIAL + TEMP_CIMA_INICIAL) / 2, TEMP_CIMA_INICIAL + 1))
        self.set("temp_min", random.uniform(TEMP_BAIXO_INICIAL, (TEMP_CIMA_INICIAL + TEMP_BAIXO_INICIAL) / 2))
        self.set("esp", random.choice(ESPECIALIDADES))

        self.registar_unidade = self.RegistarNaUnidade()
        self.esperar_tratamento = self.EsperarTratamento()
        libertar_cama = self.LibertarCama()
        self.add_behaviour(self.registar_unidade)
        self.add_behaviour(self.esperar_tratamento)
        self.add_behaviour(libertar_cama)


    # Função para geração de dados médicos
    def mensagem_dados(self): # PODE SER ISTO QUE CAUSA OS ERROS COM O RANDOM
        dados = Message(to=AGENTE_MONITOR)
        dados.set_metadata("performative", "inform")
        dados.set_metadata("ontology", "dados_paciente")

        dados.body = jsonpickle.encode(
            DadosPaciente(
                str(self.jid),
                self.get("esp"),
                random.randint(self.get("bpm_min"), self.get("bpm_max") + 1),
                random.randint(self.get("bf_min"), self.get("bf_max") + 1),
                random.uniform(self.get("temp_min"), self.get("temp_max") + 1),
                None
            )
        )

        return dados


    # Efetua o registo no Agente Unidade
    class RegistarNaUnidade(OneShotBehaviour):
        async def run(self):
            registo = Message(to=AGENTE_UNIDADE)
            registo.set_metadata("performative", "subscribe")
            registo.body = jsonpickle.encode(DadosPaciente(str(self.agent.jid),self.agent.get("esp"),
                                                        None,None,None,random.randint(GRAU_MIN + 1, GRAU_MAX + 1)))
            await self.send(registo)
            print(f"{extrair_nome_agente(self.agent.jid)}: Registo enviado ao Agente Unidade.")

            reply = await self.receive(timeout=10)
            if reply and reply.get_metadata("performative") == "refuse":
                print(f"{extrair_nome_agente(self.agent.jid)}: Os dados não são graves o suficiente para entrar na UCI.")
                await self.agent.stop()

            elif reply and (reply.get_metadata("performative") == "confirm") and (reply.get_metadata("ontology") == "registado"):
                print(f"{extrair_nome_agente(self.agent.jid)}: Pronto para enviar dados.")
                await self.send(self.agent.mensagem_dados())


    '''
    Aguarda a resposta aos dados médicos que enviou e envia novos
    dados ou termina a execução conforme a resposta que recebe.
    '''
    class EsperarTratamento(CyclicBehaviour):
        async def on_start(self):
            await self.agent.registar_unidade.join()

        async def run(self):
            msg = await self.receive()
            # Caso o monitor peça que não envie mais dados
            if msg and (msg.get_metadata("performative") == "refuse") and (msg.get_metadata("ontology") == "stop_dados"):
                self.kill()

            # Caso seja tratado (confirm de um Médico) ou esteja a recuperar (refuse do Monitor com ontology "novos_dados")
            elif msg and ((msg.get_metadata("performative") == "confirm") and (msg.get_metadata("ontology") == "tratado")):

                ### NOTA: ESTES CÁLCULOS ESTÃO CORRIGIDOS À PADEIRO ###
                if self.get("bpm_min") >= BPM_BAIXO_IDEAL:
                    bpm_min = int(self.agent.get("bpm_min") + K * (BPM_CIMA_IDEAL - self.agent.get("bpm_min")))
                    self.set("bpm_min", bpm_min)

                if self.get("bpm_max") <= BPM_CIMA_IDEAL:
                    bpm_max = int(self.agent.get("bpm_max") - K * (self.agent.get("bpm_max") - BPM_BAIXO_IDEAL))
                    self.set("bpm_max", bpm_max)

                if self.get("bf_min") >= BF_BAIXO_IDEAL:
                    bf_min = int(self.agent.get("bf_min") + K * (BF_CIMA_IDEAL - self.agent.get("bf_min")))
                    self.set("bf_min", bf_min)

                if self.get("bf_max") <= BF_CIMA_IDEAL:
                    bf_max = int(self.agent.get("bf_max") - K * (self.agent.get("bf_max") - BF_BAIXO_IDEAL))
                    self.set("bf_max", bf_max)

                if self.get("temp_min") >= TEMP_BAIXO_IDEAL:
                    temp_min = self.agent.get("temp_min") + K * (TEMP_CIMA_IDEAL - self.agent.get("temp_min"))
                    self.set("temp_min", temp_min)

                if self.get("temp_max") <= TEMP_CIMA_IDEAL:
                    temp_max = self.agent.get("temp_max") - K * (self.agent.get("temp_max") - TEMP_BAIXO_IDEAL)
                    self.set("temp_max", temp_max)

                await self.send(self.agent.mensagem_dados())

            elif msg and (msg.get_metadata("performative") == "refuse") and (msg.get_metadata("ontology") == "novos_dados"):
                await self.send(self.agent.mensagem_dados())


    # Termina a execução quando o Agente Unidade confirma a saída do paciente da UCI
    class LibertarCama(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg and (msg.get_metadata("performative") == "unsubscribe"):
                print(f"{extrair_nome_agente(self.agent.jid)}: ESTOU CURADO!!!!!!!!!!!!!!!!!!")
                await self.agent.stop()
