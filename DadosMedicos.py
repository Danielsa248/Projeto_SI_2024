from datetime import time


class DadosMedicos:
    def __init__(self, jid: str, especialidade: str, turno: (time, time)):
        self.jid = jid
        self.especialidade = especialidade
        self.turno = turno

    def getJid(self):
        return self.jid

    def getEspecialidade(self):
        return self.especialidade

    def getTurno(self):
        return self.turno

    def __str__(self):
        return f' {self.jid} {self.especialidade} {self.turno}'