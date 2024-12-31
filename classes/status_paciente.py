# Classe representativa do status de um Paciente para o agente Monitor

class StatusPaciente:
    def __init__(self, jid, grau, contador):
        self.jid = jid
        self.grau = grau
        self.contador = contador

    def get_jid(self):
        return self.jid

    def get_grau(self):
        return self.grau

    def get_contador(self):
        return self.contador

    def set_grau(self, grau):
        self.grau = grau

    def set_contador(self, contador):
        self.contador = contador