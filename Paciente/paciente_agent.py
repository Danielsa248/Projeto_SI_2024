from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.behaviour import PeriodicBehaviour
from spade.message import Message
import random
import jsonpickle
import infosPaciente as IP

class Paciente(Agent):

    class GerarDados(PeriodicBehaviour):
        async def run(self):
            print("Novo Cliente a ser adicionado")
            msg = Message(to="manager@win-2gse0jmk7ch")     
            msg.set_metadata("performative", "request")  
            msg.body = jsonpickle.encode(IP.infosPaciente(str(self.agent.jid),random.randint(50,201),random.randint(8,31),random.randint(33,42),random.randint(1,11)))
            await self.send(msg)

        
    class EsperarTratamento(OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                p = msg.get_metadata('performative')
                if p == 'confirm':
                    #este confirm recebe do médico, quano está curado depois pode ser eliminado (?)
                    print("")
                
                elif p == 'refuse':
                      # ver este  
                    print("grau baixo")
                
                
                else:
                    print("Did not received any message after 10 seconds")



    async def setup(self):
        print("PacienteAgent started")
        a = self.GerarDados(period=2)
        b = self.EsperarTratamento()
        self.add_behaviour(a)
        self.add_behaviour(b)
