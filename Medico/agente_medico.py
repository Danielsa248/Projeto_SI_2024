import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import jsonpickle
from DadosMedicos import *
from info_comum import *


xmp_server = "desktop-j59unhi"


class Medico(Agent):
    turnos = ["turno1", "turno2", "turno3"]

    # Gera a sua especialidade e um turno aleatoriamente
    especialidade = random.choice(ESPECIALIDADES)
    turno = random.choice(turnos)

    def setup(self):
        behave1 = self.MedicoRegista()
        behave2 = self.TrataPaciente()
        self.add_behaviour(behave1)
        self.add_behaviour(behave2)


    '''Comportamento onde o Médico envia mensagem ao Gestor para o registar no sistema'''

    class MedicoRegista(OneShotBehaviour):
        async def run(self):
            #Manda msg ao Gestor de Medicos
            mo = DadosMedicos(self.agent.jid, self.agent.especialidade, self.agent.turno)
            msg = Message(to="GestorMedicos@" + xmp_server)
            msg.body = jsonpickle.encode(mo)
            msg.set_metadata("performative", "inform")

            await self.send(msg)
            print(f"{self.agent.jid}: Registo enviado ao Gestor")
            print(f"{self.agent.jid}: Especialidade = {self.agent.especialidade} Turno = {self.agent.turno}")


    '''Comportamento onde o Médico trata o Paciente'''

    class TrataPaciente(CyclicBehaviour):
        async def run(self):
            ordem = await self.receive(timeout=5)

            # Trata do paciente
            if ordem:
                ord = ordem.get_metadata("performative")
                if ord == "inform":
                    paciente = ordem.body

                    msg = Message(to=paciente + "@" + xmp_server)
                    msg.set_metadata("performative", "confirm")

                    time.sleep(random.randint(2,10))
                    await self.send(msg)
                    print(f"{self.agent.jid}: Paciente {paciente} tratado com sucesso")

                    #Sinaliza o fim do tratamento ao Gestor de Medicos
                    msg = Message(to="GestorMedicos@" + xmp_server)
                    msg.set_metadata("performative", "confirm")
                    msg.body = self.agent.jid + "," + self.agent.especialidade
                    await self.send(msg)