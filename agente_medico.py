import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
import random
import jsonpickle
from classes.DadosMedicos import *
from info_comum import *


class Medico(Agent):
    async def setup(self):
        print(f"{self.jid}: A iniciar ...")
        # Gera a sua especialidade e um turno aleatoriamente
        self.set("esp", random.choice(ESPECIALIDADES))
        self.set("turno", random.choice(TURNOS))
        behave1 = self.MedicoRegista()
        behave2 = self.TrataPaciente()
        self.add_behaviour(behave1)
        self.add_behaviour(behave2)


    '''Comportamento onde o Médico envia mensagem ao Gestor para o registar no sistema'''

    class MedicoRegista(OneShotBehaviour):
        async def run(self):
            #Manda msg ao Gestor de Medicos
            dm = DadosMedicos(self.agent.jid, self.agent.get("esp"), self.agent.get("turno"))
            msg = Message(to=AGENTE_GESTOR_MEDICOS)
            msg.body = jsonpickle.encode(dm)
            msg.set_metadata("performative", "subscribe")

            await self.send(msg)
            print(f"{self.agent.jid}: Registo enviado ao Gestor")


    '''Comportamento onde o Médico trata o Paciente'''

    class TrataPaciente(CyclicBehaviour):
        async def run(self):
            ordem = await self.receive(timeout=5)

            # Trata do paciente
            if ordem:
                ord = ordem.get_metadata("performative")
                if ord == "inform":
                    paciente = ordem.body

                    trat = Message(to=str(paciente))
                    trat.set_metadata("performative", "confirm")
                    trat.set_metadata("ontology", "tratado")

                    time.sleep(random.randint(2,10))
                    await self.send(trat)
                    print(f"{self.agent.jid}: Paciente {paciente} tratado com sucesso")

                    # Sinaliza o fim do tratamento ao Gestor de Medicos
                    msg = Message(to=AGENTE_GESTOR_MEDICOS)
                    msg.set_metadata("performative", "confirm")
                    msg.body = str(self.agent.jid) + "," + self.agent.get("esp")
                    await self.send(msg)