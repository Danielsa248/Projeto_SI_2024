from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.behaviour import CyclicBehaviour
from datetime import time
from spade.message import Message
import random
import jsonpickle
from Medico.DadosMedicos import DadosMedicos
from SintomasTratados import SintomasTratados

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
        self.valores_normalizados = {"bpm": (), "bp": (), "bf": (), "temperatura": ()}


    class MedicoRegista(OneShotBehaviour):
        async def run(self):
            #Gera a sua especialidade e um turno aleatoriamente
            esp = random.choice(self.agent.especialidade)
            turno = random.choice(self.agent.turno)

            #Manda msg ao Gestor de Medicos
            mo = DadosMedicos(self.agent.jid, esp, turno)
            msg = Message(to="gestor_medicos@" + xmp_server)
            msg.body = jsonpickle.encode(mo)
            msg.set_metadata("performative", "inform")

            await self.send(msg)
            print(f"{self.agent.jid}: Registo enviado ao Gestor")
            print(f"{self.agent.jid}: Especialidade = {esp} Turno = {turno}")


    class MedicoTrata(CyclicBehaviour):
        async def run(self):
            ordem = await self.receive(timeout=5)

            # Trata do paciente
            if ordem:
                ord = ordem.get_metadata("performative")
                if ord == "request":
                    tratamento = jsonpickle.decode(ordem.body)
                    paciente = tratamento.getPaciente()
                    sintomas = tratamento.getSintomas()
                    sintomas_tratados = []

                    for sintoma in sintomas:
                        sintoma[1] = random.choice(self.agent.valores_normalizados[sintoma[0]]) #normalizar os dados
                        sintomas_tratados.append(sintoma)

                    mo = SintomasTratados(paciente, sintomas_tratados)
                    msg = Message(to=paciente + "@" + xmp_server)
                    msg.body = jsonpickle.encode(mo)
                    msg.set_metadata("performative", "inform")

                    time.sleep(5)
                    await self.send(msg)
                    print(f"{self.agent.jid}: Paciente {paciente} tratado")

                    #Sinaliza o fim do tratamento ao Gestor de Medicos
                    msg = Message(to="gestor_medicos@" + xmp_server)
                    msg.set_metadata("performative", "confirm")
                    await self.send(msg)