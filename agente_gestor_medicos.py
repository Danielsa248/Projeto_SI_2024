import random
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
import jsonpickle
from info_comum import *


class AgenteGestorMedicos(Agent):
    medicos = {especialidade: [] for especialidade in ESPECIALIDADES}
    turno_atual = TURNOS[0]

    async def setup(self):
        print(f"{self.jid}: A iniciar ...")
        behave1 = self.RegistaMedico()
        behave2 = self.OrdemMedico()
        behave3 = self.FimTratamento()
        behave4 = self.TrocaTurnos(period=30)
        self.add_behaviour(behave1)
        self.add_behaviour(behave2)
        self.add_behaviour(behave3)
        self.add_behaviour(behave4)


    '''Comportamento que espera Médicos para os registar no sistema'''

    class RegistaMedico(CyclicBehaviour):
        async def run(self):
            registo = await self.receive(timeout=5)

            if registo:
                reg = registo.get_metadata("performative")
                if reg == "subscribe":
                    dados = jsonpickle.decode(registo.body)
                    jid = dados.getMedico()
                    especialidade = dados.getEspecialidade()
                    turno = dados.getTurno()

                    if turno == self.agent.turno_atual:
                        self.agent.medicos[especialidade].append([jid, turno, True])

                    else:
                        self.agent.medicos[especialidade].append([jid, turno, False])


    '''Comportamento que espera requisições do Agente Alerta e 
        requisita um Médico para tratar o doente'''

    class OrdemMedico(CyclicBehaviour):
        async def run(self):
            requisicao = await self.receive(timeout=5)

            if requisicao:
                req = requisicao.get_metadata("performative")
                if req == "request":
                    dados = jsonpickle.decode(requisicao.body)
                    paciente = dados.getjid()
                    especialidade = dados.getEspecialidade()

                    med_encontrado = False
                    for med in self.agent.medicos[especialidade]:
                        if med[2]:
                            medico = med[0]
                            med[2] = False
                            med_encontrado = True
                            break

                    #Envia mensagem ao Agente Alerta para lhe informar sobre o pedido
                    msg_alerta = Message(to=AGENTE_ALERTA)

                    if med_encontrado:
                        msg_alerta.set_metadata("performative", "confirm")
                        await self.send(msg_alerta)

                        # Envia mensagem ao Médico com a informação do paciente a ser tratado
                        ordem = Message(to=medico + "@" + XMPP_SERVER)
                        ordem.set_metadata("performative", "inform")
                        ordem.body = paciente
                        await self.send(ordem)
                        print(f"{self.agent.jid}: Médico {medico} requisitado para o Paciente {paciente}")

                    else:
                        msg_alerta.set_metadata("performative", "refuse")
                        await self.send(msg_alerta)
                        print(f"{self.agent.jid}: Nenhum Médico está disponível para o Paciente {paciente}")


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
                            if med[1] == self.agent.turno_atual :
                                med[2] = True
                                print(f"{self.agent.jid}: Médico {medico} novamente disponível")
                                break


    '''Comportamento relativo à troca de turnos dos Médicos'''

    class TrocaTurnos(PeriodicBehaviour):
        async def run(self):
            if self.agent.turno_atual == TURNOS[-1]:
                self.agent.turno_atual = TURNOS[0]

            else:
                self.agent.turno_atual = TURNOS[TURNOS.index(self.agent.turno_atual) + 1]

            for especialidade in self.agent.medicos.keys():
                for med in self.agent.medicos[especialidade]:
                    if med[1] == self.agent.turno_atual:
                        med[2] = True

                    else:
                        med[2] = False