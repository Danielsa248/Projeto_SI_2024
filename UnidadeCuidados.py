import jsonpickle
import random as rand
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message


class UnidadeCuidados(Agent):

    salas = {"Cardiologia" : [{}, rand.randint(8,15)] , "Cirurgia Geral" : [{}, rand.randint(8,15)] ,
             "Gastrenterologia": [{}, rand.randint(8,15)] , "Medicina Interna": [{}, rand.randint(8,15)] ,
             "Ortopedia" : [{}, rand.randint(8,15)], "Cirurgia Cardiotorácica" : [{}, rand.randint(8,15)],
             "Cuidados Geral" : [{}, rand.randint(20,35)] }



    async def setup(self):
        print("Agent Unidade de Cuidados: {}".format(str(self.jid)) + " starting...")
        a = self.registarUtenteBehav()
        b = self.updatePrioridadeBehav()
        self.add_behaviour(a)
        self.add_behaviour(b)


    def utenteExists(self, jid):

        for values in self.agent.salas.values():
            if jid in values[0]:
                return True

    # REVER ESTA MERDA TODA...
    def reorganizeUtentes(self, especialidade, prioridade, paciente):

        min = prioridade
        id = paciente

        for key, value in self.agent.salas[especialidade][0].items():

            if value < min:
                min = value
                id = key

        if min < prioridade:

            self.agent.salas[especialidade][0].pop(id)
            self.agent.salas[especialidade][0][paciente] = prioridade

            if self.agent.salas["Cuidados Geral"][1] > 0:
                self.agent.salas["Cuidados Geral"][0][id] = min
                self.agent.salas["Cuidados Geral"][1] -= 1
                return True

            else:
                # pop menor prioridade nos cuidados geral
                min2 = min
                id2 = id

                for key, value in self.agent.salas["Cuidados Geral"][0].items():

                    if value < min2:
                        min2 = value
                        id2 = key

                if min2 < min:
                    self.agent.salas["Cuidados Geral"][0].pop(id2)
                    self.agent.salas["Cuidados Geral"][0][id] = min
                    return True

                else:
                    return False

        else:
            if self.agent.salas["Cuidados Geral"][1] > 0:
                self.agent.salas["Cuidados Geral"][0][paciente] = prioridade
                self.agent.salas["Cuidados Geral"][1] -= 1
                return True

            else:
                # pop menor prioridade nos cuidados geral
                min2 = prioridade
                id2 = paciente

                for key, value in self.agent.salas["Cuidados Geral"][0].items():

                    if value < min2:
                        min2 = value
                        id2 = key

                if min2 < prioridade:
                    self.agent.salas["Cuidados Geral"][0].pop(id2)
                    self.agent.salas["Cuidados Geral"][0][paciente] = prioridade
                    return True

                else:
                    return False




    class registarUtenteBehav(CyclicBehaviour):

        async def run(self):

            msg = await self.receive(timeout=10)
            if msg:
                msg_meta = msg.get_metadata("performative")

                if msg_meta == "subscribe":

                    utente = jsonpickle.decode(msg.body)

                    exists = self.agent.utenteExists(utente.getGID())

                    if not exists:

                        if utente.getEspecialidade() not in self.agent.salas:

                            if self.agent.salas["Cuidados Geral"][1] > 0:

                                self.agent.salas["Cuidados Geral"][0][utente.getGID()] = utente.getPrioridade()
                                self.agent.salas["Cuidados Geral"][1] -= 1
                                print("Agent {}:".format(self.agent.jid) + "registered patient Agent {}!".format(msg.sender) + "nos Cuidados Gerais")


                                #mandar confirm
                                msg_response = msg.make_reply()
                                msg_response.set_metadata("performative", "confirm")
                                await self.send(msg_response)

                            else:
                                #mudar e tirar o menor prioridade?
                                print("Agent {}:".format(self.agent.jid) + "couldn't register patient Agent {}!".format(msg.sender) + "due to lack of beds")


                                #mandar refuse
                                msg_response = msg.make_reply()
                                msg_response.set_metadata("performative", "refuse")
                                await self.send(msg_response)

                        else:
                            if self.agent.salas[utente.getEspecialidade()][1] > 0:

                                self.agent.salas[utente.getEspecialidade()][0][utente.getGID()] = utente.getPrioridade()
                                self.agent.salas[utente.getEspecialidade()][1] -= 1
                                print("Agent {}:".format(self.agent.jid) + "registered patient Agent {}!".format(msg.sender))

                                msg_response = msg.make_reply()
                                msg_response.set_metadata("performative", "confirm")
                                await self.send(msg_response)

                            else:
                                #função que distribui utentes com base nas prioridades
                                success = self.agent.reorganizeUtentes(utente.getEspecialidade(), utente.getPrioridade(), utente.getGID())

                                if success:
                                    print("Agent {}:".format(self.agent.jid) + "registered patient Agent {}!".format(msg.sender))

                                    # mandar confirm
                                    msg_response = msg.make_reply()
                                    msg_response.set_metadata("performative", "confirm")
                                    await self.send(msg_response)

                                else:
                                    print("Agent {}:".format(self.agent.jid) + "couldn't register patient Agent {}!".format(msg.sender) + "due to lack of beds")

                                    msg_response = msg.make_reply()
                                    msg_response.set_metadata("performative", "refuse")
                                    await self.send(msg_response)

                    else:
                        msg_response = msg.make_reply()
                        msg_response.set_metadata("performative", "refuse")
                        msg.body = "This patient is already registered!..."
                        await self.send(msg_response)

                else:
                    print("Agent {}:".format(str(self.agent.jid)) + " Message not understood!")
            else:
                print("Agent {}:".format(str(self.agent.jid)) + "Did not received any message after 10 seconds")



    class updatePrioridadeBehav(CyclicBehaviour):

        async def run(self):

            msg = await self.receive(timeout=10)

            if msg:
                msg_meta = msg.get_metadata("performative")

                if msg_meta == "informative":

                    utente = jsonpickle.decode(msg.body)

                    especialidade = self.getEspecialidade(utente.getGID())

                    if especialidade is not None:

                        if utente.getPrioridade() != 0:
                            self.agent.salas[especialidade][0][utente.getGID()] = utente.getPrioridade()

                        else:
                            self.agent.salas[especialidade][0].pop(utente.getGID())
                            self.agent.salas[especialidade][1] += 1
                            responde = Message(to=utente.getGID())
                            responde.set_metadata("performative", "unsubscribe")
                            await self.send(msg)

            else:
                print("Agent {}:".format(str(self.agent.jid)) + "Did not received any message after 10 seconds")


        def getEspecialidade(self, jid):

            for key, values in self.agent.salas.items():

                if jid in values[0]:
                    return key

            return None
