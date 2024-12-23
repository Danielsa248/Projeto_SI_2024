from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import jsonpickle
from DadosMedicos import *
from SintomasTratados import *


xmp_server = "desktop-j59unhi"


class Medico(Agent):
    especialidade = ["Cardiologia", "Pediatria", "Ortopedia", "Clínica", "Oftalmologia", "Dermatologia"]
    turno = [(time(6, 00), time(14, 00)),
             (time(14, 00), time(22, 00)),
             (time(22, 00), time(6, 00))]

    def __init__(self, jid, password):
        super().__init__(jid, password)
        # Gera a sua especialidade e um turno aleatoriamente
        self.especialidade = random.choice(self.especialidades)
        self.turno = random.choice(self.turnos)
        # Cada chave tem os intervalos de valores normais
        self.valores_normalizados = {"bpm": (), "bp": (), "bf": (), "temperatura": ()}

    async def run(self):
        print("----------------------")
        print("| Médico |")
        print("----------------------")
        behave1 = self.MedicoRegista(OneShotBehaviour())
        behave2 = self.TrataPaciente(CyclicBehaviour())
        self.add_behaviour(behave1)
        self.add_behaviour(behave2)


    '''Comportamento onde o Médico envia mensagem ao Gestor para o registar no sistema'''

    class MedicoRegista(OneShotBehaviour):
        async def run(self):
            #Manda msg ao Gestor de Medicos
            mo = DadosMedicos(self.agent.jid, self.agent.especialidade, self.agent.turno)
            msg = Message(to="gestor_medicos@" + xmp_server)
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
                if ord == "request":
                    tratamento = jsonpickle.decode(ordem.body)
                    paciente = tratamento.getPaciente()
                    sintomas = tratamento.getSintomas()

                    for parametro in sintomas.keys():
                        #Escolher um valor aleatório que esteja no intervalo dos normais
                        sintomas[parametro] = random.randint(self.agent.valores_normalizados[parametro][0],
                                                             self.agent.valores_normalizados[parametro][1])

                    mo = SintomasTratados(paciente, sintomas)
                    msg = Message(to=paciente + "@" + xmp_server)
                    msg.body = jsonpickle.encode(mo)
                    msg.set_metadata("performative", "inform")

                    time.sleep(5)
                    await self.send(msg)
                    print(f"{self.agent.jid}: Paciente {paciente} tratado com sucesso")

                    #Sinaliza o fim do tratamento ao Gestor de Medicos
                    msg = Message(to="gestor_medicos@" + xmp_server)
                    msg.set_metadata("performative", "confirm")
                    msg.body(self.agent.jid, self.agent.especialidade)
                    await self.send(msg)