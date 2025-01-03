from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message

import jsonpickle

try:
    from info_comum import *
except ImportError:
    from Projeto_SI_2024.info_comum import *


class AgenteGestorMedicos(Agent):
    medicos = {especialidade: [] for especialidade in ESPECIALIDADES}
    turno_atual = TURNOS[0]

    async def setup(self):
        print(f"AGENTE GESTOR MEDICOS: A iniciar...")
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
            registo = await self.receive()

            if registo:
                reg = registo.get_metadata("performative")
                if reg == "subscribe":
                    dados = jsonpickle.decode(registo.body)
                    jid = dados.get_medico()
                    especialidade = dados.get_especialidade()
                    turno = dados.get_turno()

                    if turno == self.agent.turno_atual:
                        self.agent.medicos[especialidade].append([jid, turno, True])

                    else:
                        self.agent.medicos[especialidade].append([jid, turno, False])


    '''Comportamento que espera requisições do Agente Alerta e 
        requisita um Médico para tratar o doente'''

    class OrdemMedico(CyclicBehaviour):
        async def run(self):
            requisicao = await self.receive()

            if requisicao:
                req = requisicao.get_metadata("performative")
                if req == "request":
                    dados = jsonpickle.decode(requisicao.body)
                    paciente = dados.get_jid()
                    especialidade = dados.get_especialidade()

                    med_encontrado = False
                    for med in self.agent.medicos[especialidade]:
                        if med[2]:
                            medico = med[0]
                            med[2] = False
                            med_encontrado = True
                            break

                    #Envia mensagem ao Agente Alerta para lhe informar sobre o pedido
                    msg_alerta = Message(to=AGENTE_ALERTA)
                    msg_alerta.body = jsonpickle.encode(dados)

                    if med_encontrado:
                        msg_alerta.set_metadata("performative", "confirm")
                        await self.send(msg_alerta)

                        # Envia mensagem ao Médico com a informação do paciente a ser tratado
                        ordem = Message(to=str(medico))
                        ordem.set_metadata("performative", "inform")
                        ordem.body = paciente
                        await self.send(ordem)
                        print(f"AGENTE GESTOR MEDICOS: {extrair_nome_agente(medico)} requisitado para o {extrair_nome_agente(paciente)}")

                    else:
                        print(f"AGENTE GESTOR MEDICOS: Nenhum Médico está disponível para o {extrair_nome_agente(paciente)}")
                        msg_alerta.set_metadata("performative", "refuse")
                        await self.send(msg_alerta)


    '''Comportamento que espera que um Médico termine um tratamento'''

    class FimTratamento(CyclicBehaviour):
        async def run(self):
            conclusao = await self.receive()

            if conclusao:
                con = conclusao.get_metadata("performative")
                if con == "confirm":
                    medico = conclusao.sender
                    especialidade = conclusao.body

                    for med in self.agent.medicos[especialidade]:
                        if med[0] == medico:
                            if med[1] == self.agent.turno_atual :
                                med[2] = True
                                print(f"AGENTE GESTOR MEDICOS: {extrair_nome_agente(medico)} novamente disponível")
                                break


    '''Comportamento relativo à troca de turnos dos Médicos'''

    class TrocaTurnos(PeriodicBehaviour):
        async def run(self):
            if self.agent.turno_atual == TURNOS[-1]:
                self.agent.turno_atual = TURNOS[0]
                print(f"AGENTE GESTOR MEDICOS: Turno atual --> {self.agent.turno_atual.upper()}")

            else:
                self.agent.turno_atual = TURNOS[TURNOS.index(self.agent.turno_atual) + 1]
                print(f"AGENTE GESTOR MEDICOS: Turno atual --> {self.agent.turno_atual.upper()}")

            for especialidade in self.agent.medicos.keys():
                for med in self.agent.medicos[especialidade]:
                    if med[1] == self.agent.turno_atual:
                        med[2] = True

                    else:
                        med[2] = False