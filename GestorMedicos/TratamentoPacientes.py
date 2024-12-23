#Classe para a mensagem que informa o Medico qual o Paciente e sintomas a tratar

class TratamentoPacientes:
    def __init__(self, jid: str, sintomas: dict):
        self.jid = jid
        self.sintomas = sintomas

    def getPaciente(self):
        return self.jid

    def getSintomas(self):
        return self.sintomas

    def __str__(self):
        return f' {self.jid} {self.sintomas}'