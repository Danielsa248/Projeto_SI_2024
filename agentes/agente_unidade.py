from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

import asyncio
import jsonpickle
import random as rand

try:
    from info_comum import *
except ImportError:
    from Projeto_SI_2024.info_comum import *


class AgenteUnidade(Agent):

    salas = {}

    async def setup(self):
        print(f"AGENTE UNIDADE: A iniciar...")
        '''
        for esp in ESPECIALIDADES:
            self.salas[esp] = [{}, rand.randint(8,15)]'''

        self.salas["Cuidados Gerais"] = [{}, rand.randint(20,35)]

        self.lock = asyncio.Lock()

        a = self.RegistarUtenteBehav()
        b = self.UpdatePrioridadeBehav()
        c = self.RegistarMedico()
        self.add_behaviour(a)
        self.add_behaviour(b)
        self.add_behaviour(c)


    def utenteExists(self, jid):
        for values in self.salas.values():
            if jid in values[0]:
                return True


    def reorganizeUtentes(self, especialidade, prioridade, paciente):
        lowprio = prioridade
        id = paciente

        for key, value in self.salas[especialidade][0].items():

            if value < lowprio:
                lowprio = value
                id = key

        if lowprio < prioridade:

            self.salas[especialidade][0].pop(id)
            self.salas[especialidade][0][paciente] = prioridade

            if self.salas["Cuidados Gerais"][1] > 0:
                self.salas["Cuidados Gerais"][0][id] = lowprio
                self.salas["Cuidados Gerais"][1] -= 1
                return [id, "cuidados_gerais"]

            else:
                # pop menor prioridade nos Cuidados Gerais
                lowprio2 = lowprio
                id2 = id

                for key, value in self.salas["Cuidados Gerais"][0].items():

                    if value < lowprio2:
                        lowprio2 = value
                        id2 = key

                if lowprio2 < lowprio:
                    self.salas["Cuidados Gerais"][0].pop(id2)
                    self.salas["Cuidados Gerais"][0][id] = lowprio


                return [id2, "expulso"]

        else:
            if self.salas["Cuidados Gerais"][1] > 0:
                self.salas["Cuidados Gerais"][0][paciente] = prioridade
                self.salas["Cuidados Gerais"][1] -= 1
                return [None, "no"]

            else:
                # pop menor prioridade nos Cuidados Gerais
                lowprio2 = prioridade
                id2 = paciente

                for key, value in self.salas["Cuidados Gerais"][0].items():

                    if value < lowprio2:
                        lowprio2 = value
                        id2 = key

                if lowprio2 < prioridade:
                    self.salas["Cuidados Gerais"][0].pop(id2)
                    self.salas["Cuidados Gerais"][0][paciente] = prioridade
                    return [id2, "expulso"]

                else:
                    return None


    def getEspecialidade(self, jid):
        for key, values in self.salas.items():

            if jid in values[0]:
                return key

        return None


    class RegistarUtenteBehav(CyclicBehaviour):
        async def run(self):
            async with self.agent.lock:
                msg = await self.receive()
                if msg and (msg.get_metadata("performative") == "subscribe") and (msg.get_metadata("ontology") == "registar_paciente"):
                    utente = jsonpickle.decode(msg.body)

                    exists = self.agent.utenteExists(utente.get_jid())

                    if not exists:

                        if utente.get_especialidade() not in self.agent.salas:

                            if self.agent.salas["Cuidados Gerais"][1] > 0:

                                self.agent.salas["Cuidados Gerais"][0][utente.get_jid()] = utente.get_grau()
                                self.agent.salas["Cuidados Gerais"][1] -= 1
                                print(f"AGENTE UNIDADE: Registou {extrair_nome_agente(msg.sender)}.")

                                #mandar confirm
                                msg_response = msg.make_reply()
                                msg_response.set_metadata("performative", "confirm")
                                msg_response.set_metadata("ontology", "cuidados_gerais")
                                await self.send(msg_response)

                            else:
                                #mudar e tirar o menor prioridade?
                                print(f"AGENTE UNIDADE: Não conseguiu registar {extrair_nome_agente(msg.sender)} devido à falta de camas.")


                                #mandar refuse
                                msg_response = msg.make_reply()
                                msg_response.set_metadata("performative", "refuse")
                                await self.send(msg_response)

                        else:
                            if self.agent.salas[utente.get_especialidade()][1] > 0:

                                self.agent.salas[utente.get_especialidade()][0][utente.get_jid()] = utente.get_grau()
                                self.agent.salas[utente.get_especialidade()][1] -= 1
                                print(f"AGENTE UNIDADE: Registou {extrair_nome_agente(msg.sender)}.")

                                msg_response = msg.make_reply()
                                msg_response.set_metadata("performative", "confirm")
                                msg_response.set_metadata("ontology", "registado")
                                await self.send(msg_response)

                            else:
                                #função que distribui utentes com base nas prioridades
                                success = self.agent.reorganizeUtentes(utente.get_especialidade(), utente.get_grau(), utente.get_jid())

                                if success:
                                    print(f"AGENTE UNIDADE: Registou {extrair_nome_agente(msg.sender)}.")

                                    if success[1] == "no":
                                        response = msg.make_reply()
                                        response.set_metadata("performative", "confirm")
                                        response.set_metadata("ontology", "cuidados_gerais")
                                        await self.send(response)

                                    elif success[1] == "expulso":
                                        msg_expulso = Message(to=success[0])
                                        msg_expulso.set_metadata("performative", "unsubscribe")
                                        msg_expulso.set_metadata("ontology", "transferido")
                                        await self.send(msg_expulso)

                                        response = msg.make_reply()
                                        response.set_metadata("performative", "confirm")
                                        response.set_metadata("ontology", "cuidados_gerais")
                                        await self.send(response)

                                    elif success[1] == "cuidados_gerais":
                                        msg_cg = Message(to=success[0])
                                        msg_cg.set_metadata("performative", "confirm")
                                        msg_cg.set_metadata("ontology", "cuidados_gerais")
                                        await self.send(msg_cg)

                                else:
                                    print(f"AGENTE UNIDADE: Não conseguiu registar {extrair_nome_agente(msg.sender)} devido à falta de camas.")

                                    msg_response = msg.make_reply()
                                    msg_response.set_metadata("performative", "refuse")
                                    await self.send(msg_response)

                    else:
                        msg_response = msg.make_reply()
                        msg_response.set_metadata("performative", "refuse")
                        msg.body = "Este paciente já está registado!..."
                        await self.send(msg_response)


    class RegistarMedico(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)

            if msg and (msg.get_metadata("performative") == "subscribe") and (msg.get_metadata("ontology") == "registar_medico"):
                medico = jsonpickle.decode(msg.body)
                especialidade = medico.get_especialidade()

                if especialidade != "Cuidados Gerais":
                    if especialidade not in self.agent.salas.keys():
                        self.agent.salas[especialidade] = [{}, rand.randint(8,15)]


    class UpdatePrioridadeBehav(CyclicBehaviour):
        async def run(self):
            async with self.agent.lock:
                msg = await self.receive(timeout=10)

                if msg and (msg.get_metadata("performative") == "inform"):
                    utente = jsonpickle.decode(msg.body)

                    especialidade = self.agent.getEspecialidade(utente.get_jid())

                    if especialidade is not None:

                        if utente.get_grau() != 0:
                            self.agent.salas[especialidade][0][utente.get_jid()] = utente.get_grau()

                        else:
                            self.agent.salas[especialidade][0].pop(utente.get_jid())
                            self.agent.salas[especialidade][1] += 1
                            responde = Message(to=utente.get_jid())
                            responde.set_metadata("performative", "unsubscribe")
                            responde.set_metadata("ontology", "curado")
                            await self.send(responde)
