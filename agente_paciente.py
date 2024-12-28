from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour, OneShotBehaviour
from spade.message import Message
import random
import jsonpickle
from classes.infosPaciente import *
from info_comum import *


class Paciente(Agent):

    async def setup(self):
        print(f"{self.jid}: A iniciar ...")
        self.set("bpm", random.randint(BPM_BAIXO_INICIAL,BPM_CIMA_INICIAL))
        self.set("bf", random.randint(BF_BAIXO_INICIAL,BF_CIMA_INICIAL))
        self.set("temp", random.randint(TEMP_BAIXO_INICIAL,TEMP_CIMA_INICIAL))
        self.set("esp", random.choice(ESPECIALIDADES))

        registar_unidade = self.RegistarNaUnidade()
        esperar_tratamento = self.EsperarTratamento()
        self.enviar_dados = self.EnviarDados()
        libertar_cama = self.LibertarCama()
        self.add_behaviour(registar_unidade)
        self.add_behaviour(esperar_tratamento)
        self.add_behaviour(self.enviar_dados)
        self.add_behaviour(libertar_cama)


    class RegistarNaUnidade(OneShotBehaviour):           # este OneShotBehaviour é para fazer o registo na unidade
        async def run(self):
            msg1 = Message(to=AGENTE_UNIDADE)
            msg1.set_metadata("performative", "subscribe")
            msg1.body = jsonpickle.encode(infosPaciente(str(self.agent.jid),self.agent.get("esp"),
                                                        None,None,None,random.randint(GRAU_MIN,GRAU_MAX + 1)))
            await self.send(msg1)
            print(f"{self.agent.jid}: Registo enviado à Unidade")

            reply = await self.receive()
            if reply and reply.get_metadata("performative") == "refuse":
                await self.agent.stop()

            elif reply and (reply.get_metadata("performative") == "confirm") and (reply.get_metadata("ontology") == "registado"):
                await self.agent.enviar_dados.join()



    class EnviarDados(OneShotBehaviour):
        async def run(self):
            msg2 = Message(to=AGENTE_MONITOR)
            msg2.set_metadata("performative", "inform")
            msg2.set_metadata("ontology", "dados_paciente")
            msg2.body = jsonpickle.encode(
                infosPaciente(str(self.agent.jid), self.agent.get("esp"), self.agent.get("bpm"),
                              self.agent.get("bf"), self.agent.get("temp"), None))
            await self.send(msg2)
            print(f"{self.agent.jid}: Dados enviados ao Monitor")


    class EsperarTratamento(CyclicBehaviour):
        async def run(self):
            msg = await self.receive()
            print(f"{self.agent.jid}: Tenho esta msg - {msg}")
            if msg and (msg.get_metadata("performative") == "confirm") and (msg.get_metadata("ontology") == "tratado"):
                bpm_min = BPM_BAIXO_INICIAL + (0.1 * (BPM_BAIXO_IDEAL - BPM_BAIXO_INICIAL))
                bpm_max = BPM_CIMA_INICIAL - (0.2 * (BPM_CIMA_INICIAL - BPM_CIMA_IDEAL))
                self.set("bpm", random.randint(bpm_min, bpm_max))

                bf_min = BF_BAIXO_INICIAL + 1
                bf_max = BF_CIMA_INICIAL - 1
                self.set("bf", random.randint(bf_min, bf_max))

                temp_min = TEMP_BAIXO_INICIAL + 1
                temp_max = TEMP_CIMA_INICIAL - 1
                self.set("temp", random.randint(temp_min, temp_max))

            await self.agent.enviar_dados.join()


    class LibertarCama(CyclicBehaviour):
        async def run(self):
            msg = await self.receive()
            if msg:
                p = msg.get_metadata('performative')
                if p == 'unsubscribe':
                    print(f"{self.agent.jid}: Estou curado")
                    await self.agent.stop()