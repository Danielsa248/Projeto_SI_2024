from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from datetime import datetime
import jsonpickle
from TratamentoPacientes import *


xmp_server = "desktop-j59unhi"


class GestorMedicos(Agent):
    async def run(self):
        print("----------------------")
        print("| Gestor de Médicos |")
        print("----------------------")
        behave1 = self.RegistaMedico(CyclicBehaviour())
        behave2 = self.OrdemMedico(CyclicBehaviour())
        behave3 = self.FimTratamento(CyclicBehaviour())
        self.add_behaviour(behave1)
        self.add_behaviour(behave2)
        self.add_behaviour(behave3)
        self.medicos = {"Cardiologia":[], "Pediatria": [], "Ortopedia": [],
                        "Clínica": [], "Oftalmologia": [], "Dermatologia": []}


    '''Comportamento que espera Médicos para os registar no sistema'''

    class RegistaMedico(CyclicBehaviour):
        async def run(self):
            registo = await self.receive(timeout=5)

            if registo:
                reg = registo.get_metadata("performative")
                if reg == "inform":
                    dados = jsonpickle.decode(registo.body)
                    jid = dados.getMedico()
                    especialidade = dados.getEspecialidade()
                    turno = dados.getTurno()

                    #Turno normal
                    if turno[0] < turno[1]:
                        if turno[0] <= datetime.now().time() < turno[1]:
                            disp = True

                    #Turno durante a meia-noite
                    else:
                        if turno[0] <= datetime.now().time() or datetime.now().time() < turno[1]:
                            disp = True

                    self.agent.medicos[especialidade].append([jid, disp])


    '''Comportamento que espera requisições do Agente Alerta e 
        requisita um Médico para tratar o doente'''

    class OrdemMedico(CyclicBehaviour):
        async def run(self):
            requisicao = await self.receive(timeout=5)

            if requisicao:
                req = requisicao.get_metadata("performative")
                if req == "request":
                    dados = jsonpickle.decode(requisicao.body)
                    paciente = dados.getPaciente()
                    especialidade = dados.getEspecialidade()
                    sintomas = dados.getSintomas()

                    ordem = TratamentoPacientes(paciente, sintomas)

                    meds_disp = False
                    for medico in self.agent.medicos[especialidade].values():
                        if medico[1] == True:
                            medico = self.agent.medicos[especialidade][0]
                            medico[1] = False
                            meds_disp = True
                            break

                    if not meds_disp:
                        for medico in self.agent.medicos["Clínica"].values():
                            if medico[1] == True:
                                medico = self.agent.medicos[especialidade][0]
                                medico[1] = False
                                meds_disp = True
                                break

                    msg = Message(to= medico + "@" + xmp_server)
                    msg.body = jsonpickle.encode(ordem)
                    msg.set_metadata("performative", "request")

                    await self.send(msg)
                    print(f"{self.agent.jid}: Médico {medico} requisitado para o Paciente {paciente}")


    '''Comportamento que espera que um Médico termine um tratamento'''

    class FimTratamento(CyclicBehaviour):
        async def run(self):
            conclusao = await self.receive(timeout=5)

            if conclusao:
                con = conclusao.get_metadata("performative")
                if con == "confirm":
                    info = conclusao.body.split(",")
                    medico = info[0]
                    especialidade = info[1]

                    for med in self.agent.medicos[especialidade]:
                        if med[0] == medico:
                            med[1] = True
                            break

                    print(f"{self.agent.jid}: Médico {medico} novamente disponível")