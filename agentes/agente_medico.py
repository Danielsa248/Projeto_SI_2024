from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message

import random
import jsonpickle
import asyncio

try:
    from info_comum import *
    from classes.dados_medico import *
except ImportError:
    from Projeto_SI_2024.info_comum import *
    from Projeto_SI_2024.classes.dados_medico import *


class AgenteMedico(Agent):
    async def setup(self):
        print(f"{extrair_nome_agente(self.jid)}: A iniciar...")
        # Gera a sua especialidade e um turno aleatoriamente
        self.set("esp", random.choice(ESPECIALIDADES))
        self.set("turno", random.choice(TURNOS))
        self.behave1 = self.MedicoRegista()
        behave2 = self.TrataPaciente()
        self.add_behaviour(self.behave1)
        self.add_behaviour(behave2)


    '''Comportamento onde o Médico envia mensagem ao Gestor para o registar no sistema'''

    class MedicoRegista(OneShotBehaviour):
        async def run(self):
            #Manda msg ao Gestor de Medicos
            dm = DadosMedicos(str(self.agent.jid), self.agent.get("esp"), self.agent.get("turno"))
            msg = Message(to=AGENTE_GESTOR_MEDICOS)
            msg.body = jsonpickle.encode(dm)
            msg.set_metadata("performative", "subscribe")

            await self.send(msg)
            print(f"{extrair_nome_agente(self.agent.jid)}: Registo enviado ao Gestor")


    '''Comportamento onde o Médico trata o Paciente'''

    class TrataPaciente(CyclicBehaviour):
        async def on_start(self):
            await self.agent.behave1.join()

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

                    await asyncio.sleep(random.randint(2,10))
                    await self.send(trat)
                    print(f"{extrair_nome_agente(self.agent.jid)}: {extrair_nome_agente(paciente)} tratado com sucesso")

                    # Sinaliza o fim do tratamento ao Gestor de Medicos
                    msg = Message(to=AGENTE_GESTOR_MEDICOS)
                    msg.set_metadata("performative", "confirm")
                    msg.body = str(self.agent.jid) + "," + self.agent.get("esp")
                    await self.send(msg)