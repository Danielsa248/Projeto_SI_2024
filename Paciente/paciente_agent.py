from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour, OneShotBehaviour
from spade.message import Message
import random
import jsonpickle
import infosPaciente as IP
import info_comum as ic
import asyncio

class Paciente(Agent):


    class GerarDados(OneShotBehaviour):           # este OneShotBehaviour é para fazer o registo na unidade
        async def run(self):
            print("Novo Paciente a ser adicionado à unidade")                      
            msg1 = Message(to=ic.AGENTE_UNIDADE)   
            msg1.set_metadata("performative", "inform")  
            msg1.body = jsonpickle.encode(IP.infosPaciente(str(self.agent.jid),random.choice(ic.ESPECIALIDADES),None,None,None,random.randint(ic.GRAU_MIN,ic.GRAU_MAX)))
            await self.send(msg1)
            print("Registo de Paciente "+ str(self.agent.jid) + " enviado à Unidade")

    ## e por isto em join dentro da cena do paciente?
    class DadosAMonitorizar(PeriodicBehaviour):    
            async def run(self):     
                msg2 = Message(to=ic.AGENTE_MONITOR)   
                msg2.set_metadata("performative", "inform")  
                msg2.set_metadata("ontology", "dados_paciente")
                msg2.body = jsonpickle.encode(IP.infosPaciente(str(self.agent.getjid()),random.choice(ic.ESPECIALIDADES),random.randint(40,221),random.randint(6,34),random.randint(30,44),self.agent.getgrauPrioridade()))
                await self.send(msg2)
                print("Monitorizacão do paciente "+str(self.agent.jid)+" enviada ao monitor")  
                                    



 # o periodic so comeca depois do await, no fim de desse behaviour, ou seja, no fim do monitor, se o monitor disser que sim, ele gera novos dados 
    class LibertaCama(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                p = msg.get_metadata('performative')
                if p == 'unsubscribe':
                    # aqui manda mensagem à unidade para eliminar este paciente da base de dados dos pacientes
                    msg = Message(to=ic.AGENTE_UNIDADE)     
                    msg.set_metadata("performative", "request")  
                    msg.body = (str(self.getjid())) # adicionar aqui o jid para ele saber o que tem de eliminar
                    await self.send(msg)
                    await asyncio.sleep(2)
                    print("Confirmação: Paciente teve alta hospitalar, saiu da unidade de saúde")
                    await self.agent.stop()


        
    class EsperarTratamento(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                p = msg.get_metadata('performative')
                if p == 'confirm':    

                    inf= jsonpickle.decode(msg.body)

                    ic.bpmbaixoinicial = ic.bpmbaixoinicial + (0.1 * (ic.bpmbaixo_ideal - ic.bpmbaixoinicial))
                    ic.bpmcimainicial =  ic.bpmcimainicial - (0.2 * (ic.bfcimainicial - ic.bpmcima_ideal))
                    bpm = random.randint(ic.bfbaixoinicial,ic.bpmcimainicial)

                    ic.bfbaixoinicial =+ 1
                    ic.bfcimainicial =- 1
                    bf = random.randint(ic.bfbaixoinicial,ic.bfcimainicial)


                    ic.tempbaixoinicial =+ 1
                    ic.tempcimainicial =- 1
                    temperatura = random.randint(ic.tempbaixoinicial,ic.tempcimainicial)

                    jid = inf.getjid() 
                    grauPrioridade = inf.getgrauPrioridade()
                    esp = inf.getespecialidade()



                    msg = Message(to=ic.AGENTE_MONITOR)     #ver esta parte, qual é o codigo do server
                    msg.set_metadata("performative", "inform")  
                    msg.body = jsonpickle.encode((jid,esp,bpm,bf,temperatura,grauPrioridade))  #aqui envia novos dados
                    await self.send(msg)
                    print("Novos dados enviados ao Monitor")
                
                
                #elif p == 'refuse':
                #   
                #    # aqui manda mensagem ao monitor para eliminar este paciente da base de dados dos pacientes
                #    msg = Message(to=ic.AGENTE_MONITOR)     
                #    msg.set_metadata("performative", "request")  
                #    msg.body = (str(self.getjid())) # adicionar aqui o jid para ele saber o que tem de eliminar
                #    await self.send(msg)
                #    time.sleep(2)
                #    print("Confirmação: Paciente teve alta hospitalar, saiu do sistema de monitorização")
                #    await self.agent.stop()
                


                else:
                    print("Did not received any message after 10 seconds")
                


    async def setup(self):
        print("PacienteAgent started")
        a = self.GerarDados()
        b = self.EsperarTratamento()
        c = self.DadosAMonitorizar(period=2)
        d = self.LibertaCama()
        self.add_behaviour(a)
        self.add_behaviour(b)
        self.add_behaviour(c)
        self.add_behaviour(d)
