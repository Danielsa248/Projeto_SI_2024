import jsonpickle
import random as rand
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from info_comum import *


class UnidadeCuidados(Agent):

    salas = {}

    async def setup(self):
        print("Agent Unidade de Cuidados: {}".format(self.jid) + " starting...")

        for esp in ESPECIALIDADES:
            self.salas[esp] = [{}, rand.randint(8,15)]

        self.salas["Cuidados Geral"] = [{}, rand.randint(20,35)]


        a = self.registarUtenteBehav()
        b = self.updatePrioridadeBehav()
        self.add_behaviour(a)
        self.add_behaviour(b)


    def utenteExists(self, jid):

        for values in self.salas.values():
            if jid in values[0]:
                return True

    # REVER ESTA MERDA TODA...
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

            if self.salas["Cuidados Geral"][1] > 0:
                self.salas["Cuidados Geral"][0][id] = lowprio
                self.salas["Cuidados Geral"][1] -= 1
                return True

            else:
                # pop menor prioridade nos cuidados geral
                lowprio2 = lowprio
                id2 = id

                for key, value in self.salas["Cuidados Geral"][0].items():

                    if value < lowprio2:
                        lowprio2 = value
                        id2 = key

                if lowprio2 < lowprio:
                    self.salas["Cuidados Geral"][0].pop(id2)
                    self.salas["Cuidados Geral"][0][id] = lowprio


                return True

        else:
            if self.salas["Cuidados Geral"][1] > 0:
                self.salas["Cuidados Geral"][0][paciente] = prioridade
                self.salas["Cuidados Geral"][1] -= 1
                return True

            else:
                # pop menor prioridade nos cuidados geral
                lowprio2 = prioridade
                id2 = paciente

                for key, value in self.salas["Cuidados Geral"][0].items():

                    if value < lowprio2:
                        lowprio2 = value
                        id2 = key

                if lowprio2 < prioridade:
                    self.salas["Cuidados Geral"][0].pop(id2)
                    self.salas["Cuidados Geral"][0][paciente] = prioridade
                    return True

                else:
                    return False


    def getEspecialidade(self, jid):

        for key, values in self.salas.items():

            if jid in values[0]:
                return key

        return None


    class registarUtenteBehav(CyclicBehaviour):

        async def run(self):

            msg = await self.receive(timeout=10)
            if msg:
                msg_meta = msg.get_metadata("performative")

                if msg_meta == "subscribe":

                    utente = jsonpickle.decode(msg.body)

                    exists = self.agent.utenteExists(utente.getjid())

                    if not exists:

                        if utente.getespecialidade() not in self.agent.salas:

                            if self.agent.salas["Cuidados Geral"][1] > 0:

                                self.agent.salas["Cuidados Geral"][0][utente.getjid()] = utente.getgrauPrioridade()
                                self.agent.salas["Cuidados Geral"][1] -= 1
                                print("Agente {}:".format(self.agent.jid) + "registou paciente {}!".format(msg.sender))


                                #mandar confirm
                                msg_response = msg.make_reply()
                                msg_response.set_metadata("performative", "confirm")
                                await self.send(msg_response)

                            else:
                                #mudar e tirar o menor prioridade?
                                print("Agente {}:".format(self.agent.jid) + "não conseguiu registar paciente{}!".format(msg.sender) + "devido a falta de camas")


                                #mandar refuse
                                msg_response = msg.make_reply()
                                msg_response.set_metadata("performative", "refuse")
                                await self.send(msg_response)

                        else:
                            if self.agent.salas[utente.getespecialidade()][1] > 0:

                                self.agent.salas[utente.getespecialidade()][0][utente.getjid()] = utente.getgrauPrioridade()
                                self.agent.salas[utente.getespecialidade()][1] -= 1
                                print("Agente {}:".format(self.agent.jid) + "registou paciente {}!".format(msg.sender))

                                msg_response = msg.make_reply()
                                msg_response.set_metadata("performative", "confirm")
                                await self.send(msg_response)

                            else:
                                #função que distribui utentes com base nas prioridades
                                success = self.agent.reorganizeUtentes(utente.getespecialidade(), utente.getgrauPrioridade(), utente.getjid())

                                if success:
                                    print("Agente {}:".format(self.agent.jid) + "registou paciente {}!".format(msg.sender))

                                    # mandar confirm
                                    msg_response = msg.make_reply()
                                    msg_response.set_metadata("performative", "confirm")
                                    await self.send(msg_response)

                                else:
                                    print("Agente {}:".format(self.agent.jid) + "não conseguiu registar paciente{}!".format(msg.sender) + "devido a falta de camas")

                                    msg_response = msg.make_reply()
                                    msg_response.set_metadata("performative", "refuse")
                                    await self.send(msg_response)

                    else:
                        msg_response = msg.make_reply()
                        msg_response.set_metadata("performative", "refuse")
                        msg.body = "Este paciente já está registado!..."
                        await self.send(msg_response)

            else:
                print("Agente {}:".format(self.agent.jid) + "não recebeu nenhuma mensagem passado 10 segundos")



    class updatePrioridadeBehav(CyclicBehaviour):

        async def run(self):

            msg = await self.receive(timeout=10)

            if msg:
                msg_meta = msg.get_metadata("performative")

                if msg_meta == "informative":

                    utente = jsonpickle.decode(msg.body)

                    especialidade = self.agent.getEspecialidade(utente.getjid())

                    if especialidade is not None:

                        if utente.getgrauPrioridade() != 0:
                            self.agent.salas[especialidade][0][utente.getjid()] = utente.getgrauPrioridade()

                        else:
                            self.agent.salas[especialidade][0].pop(utente.getjid())
                            self.agent.salas[especialidade][1] += 1
                            responde = Message(to=utente.getjid())
                            responde.set_metadata("performative", "unsubscribe")
                            await self.send(msg)

            else:
                print("Agente {}:".format(self.agent.jid) + "não recebeu nenhuma mensagem passado 10 segundos")
