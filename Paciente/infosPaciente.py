class infosPaciente:
    def __init__(self,jid,bpm,bf,temperatura,grauPrioridade):
        self.jid = jid
        self.bpm = bpm
        self.bf = bf
    #    self.bp = bp
        self.temperatura = temperatura
        self.grauPrioridade = grauPrioridade
        

    def getjid(self):
        return self.jid  
    def getbpm(self):
        return self.bpm     # batimentos por minuto  (50 e 200)
    def getbf(self):
        return self.bf      # breath frequency     (8 e 30)
    #def getbp(self):
    #    return self.bp        # blood pressure   (100 e 180)/(70 e 110)
    def gettemperatura(self):
        return self.temperatura       # temperatura corporal  (33 e 42)
    def getgrauPrioridade(self):
        return self.grauPrioridade     # grau de prioridade   (1 e 10)

    def setjid(self,jid):
        self.jid = jid    
    def setbpm(self,bpm):
        self.bpm = bpm
    def setbf(self,bf):
        self.bf = bf
    #def setbp(self,bp):
    #    self.bp = bp
    def settemperatura(self,temperatura):
        self.temperatura = temperatura
    def setgrauPrioridade(self,grauPrioridade):
        self.grauPrioridade = grauPrioridade
