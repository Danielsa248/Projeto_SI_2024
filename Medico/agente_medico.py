import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
import random
import jsonpickle
from DadosMedicos import *
from info_comum import *


class Medico(Agent):
    # Gera a sua especialidade e um turno aleatoriamente
    especialidade = random.choice(ESPECIALIDADES)
    turno = random.choice(TURNOS)

    def setup(self):
        behave1 = self.MedicoRegista()
        behave2 = self.TrataPaciente()
        self.add_behaviour(behave1)
        self.add_behaviour(behave2)


    '''Comportamento onde o Médico envia mensagem ao Gestor para o registar no sistema'''

    class MedicoRegista(OneShotBehaviour):
        async def run(self):
            #Manda msg ao Gestor de Medicos
            dm = DadosMedicos(self.agent.jid, self.agent.especialidade, self.agent.turno)
            msg = Message(to="GestorMedicos@" + XMPP_SERVER)
            msg.body = jsonpickle.encode(dm)
            msg.set_metadata("performative", "inform")

            await self.send(msg)
            print(f"{self.agent.jid}: Registo enviado ao Gestor")
            print(f"{self.agent.jid}: Especialidade = {self.agent.especialidade} | Turno = {self.agent.turno}")


    '''Comportamento onde o Médico trata o Paciente'''

    class TrataPaciente(CyclicBehaviour):
        async def run(self):
            ordem = await self.receive(timeout=5)

            # Trata do paciente
            if ordem:
                ord = ordem.get_metadata("performative")
                if ord == "inform":
                    paciente = ordem.body

                    trat = Message(to=paciente + "@" + XMPP_SERVER)
                    trat.set_metadata("performative", "confirm")

                    time.sleep(random.randint(2,10))
                    await self.send(trat)
                    print(f"{self.agent.jid}: Paciente {paciente} tratado com sucesso")

                    # Sinaliza o fim do tratamento ao Gestor de Medicos
                    msg = Message(to="GestorMedicos@" + XMPP_SERVER)
                    msg.set_metadata("performative", "confirm")
                    msg.body = self.agent.jid + "," + self.agent.especialidade
                    await self.send(msg)