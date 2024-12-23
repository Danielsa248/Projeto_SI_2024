from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.behaviour import CyclicBehaviour
from datetime import time
from spade.message import Message
import random
import jsonpickle
from DadosMedicos import DadosMedicos


xmp_server = "desktop-j59unhi"


class Medico(Agent):
    async def run(self):
        print("----------------------")
        print("| Médico |")
        print("----------------------")
        behave1 = self.MedicoRegista(OneShotBehaviour())
        behave2 = self.MedicoTrata(CyclicBehaviour())
        self.add_behaviour(behave1)
        self.add_behaviour(behave2)
        self.especialidade = ["Cardiologia", "Pediatria", "Ortopedia", "Clínica", "Oftalmologia", "Dermatologia"]
        self.turno = [(time(7, 00), time(13,00)),
                      (time(13, 00), time(19, 00)),
                      (time(19, 00), time(7, 00))]


    class MedicoRegista(OneShotBehaviour):
        async def run(self):
            #Gera a sua especialidade e um turno aleatoriamente
            esp = random.choice(self.agent.especialidade)
            turno = random.choice(self.agent.turno)

            #Manda msg ao Gestor de Médicos
            mo = DadosMedicos(self.agent.jid, esp, turno)
            msg = Message(to="gestor_medicos@" + xmp_server)
            msg.body = jsonpickle.encode(mo)
            msg.set_metadata("performative", "inform")

            await self.send(msg)
            print(f"{self.agent.jid}: Registo enviado ao Gestor")
            print(f"{self.agent.jid}: Especialidade = {esp} Turno = {turno}")


    class MedicoTrata(CyclicBehaviour):
        async def run(self):
            