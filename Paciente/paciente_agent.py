from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.behaviour import PeriodicBehaviour
from spade.message import Message
import random
import jsonpickle
import time
import infosPaciente as IP

class Paciente(Agent):

    class GerarDados(PeriodicBehaviour):
        async def run(self):
            print("Novo Paciente a ser adicionado")
            msg = Message(to="monitor@desktop-j59unhi")     #ver esta parte, qual é o codigo do server
            msg.set_metadata("performative", "inform")  
            msg.body = jsonpickle.encode(IP.infosPaciente(str(self.agent.jid),random.randint(40,221),random.randint(6,34),random.randint(30,44),random.randint(1,11)))
            await self.send(msg)
            print("Registo de Paciente enviado ao Monitor")

        
    class EsperarTratamento(OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                p = msg.get_metadata('performative')
                if p == 'confirm':      #"o médico, na linha 75, podia mandar um confirm"     
                    

                    # aqui manda mensagem ao monitor para eliminar este paciente da base de dados dos pacientes
                    msg = Message(to="monitor@desktop-j59unhi")     
                    msg.set_metadata("performative", "request")  
                    msg.body = "EliminarPaciente" # adicionar aqui o jid para ele saber o que tem de eliminar
                    await self.send(msg)
                    time.sleep(2)
                    print("Confirmação: Paciente teve alta hospitalar")


                
                elif p == 'refuse':
                # se aqui há refuse, é porque o paciente ainda não foi tratado, por isso vamos criar dados novos e por o grau de prioridade mais baixo
                    print("Paciente com tratamento não concluído, a realizar novos exames...")

                #aqui pode receber de volta os dados e altera
                    inf= jsonpickle.decode(msg.body)
                    bpm = random.randint(40,221)
                    bf = random.randint(6,34)
                    temperatura = random.randint(30,44)
                    grauPrioridade = random.randint(inf.getgrauPrioridade(),11)  #aqui cria o grau de prioridade menor (valor mais alto)
                    jid = inf.getjid() 



                    msg = Message(to="monitor@desktop-j59unhi")     #ver esta parte, qual é o codigo do server
                    msg.set_metadata("performative", "inform")  
                    msg.body = jsonpickle.encode((jid,bpm,bf,temperatura,grauPrioridade))  #aqui envia novos dados
                    await self.send(msg)
                    print("Novos dados enviados ao Monitor")
                
                
                else:
                    print("Did not received any message after 10 seconds")



    async def setup(self):
        print("PacienteAgent started")
        a = self.GerarDados(period=2)
        b = self.EsperarTratamento()
        self.add_behaviour(a)
        self.add_behaviour(b)
