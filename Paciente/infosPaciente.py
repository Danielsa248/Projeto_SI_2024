class infosPaciente:
    def __init__(self,jid,especialidade,bpm,bf,temperatura,grauPrioridade):
        self.jid = jid
        self.especialidade = especialidade
        self.bpm = bpm
        self.bf = bf
        self.temperatura = temperatura
        self.grauPrioridade = grauPrioridade
        

    def getjid(self):
        return self.jid  
    def getespecialidade(self):
        return self.especialidade 
    def getbpm(self):
        return self.bpm     # batimentos por minuto  (50 e 200)
    def getbf(self):
        return self.bf      # breath frequency     (8 e 30)
    def gettemperatura(self):
        return self.temperatura       # temperatura corporal  (33 e 42)
    def getgrauPrioridade(self):
        return self.grauPrioridade     # grau de prioridade   (1 e 10)

    def setjid(self,jid):
        self.jid = jid 
    def setespecialidade(self,especialidade):
        self.especialidade = especialidade    
    def setbpm(self,bpm):
        self.bpm = bpm
    def setbf(self,bf):
        self.bf = bf
    def settemperatura(self,temperatura):
        self.temperatura = temperatura
    def setgrauPrioridade(self,grauPrioridade):
        self.grauPrioridade = grauPrioridade

