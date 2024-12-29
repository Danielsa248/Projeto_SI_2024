#Classe para a mensagem que o Medico envia ao Gestor Medico para efetuar o registo com os seus dados

class DadosMedicos:
    def __init__(self, jid: str, especialidade: str, turno: str):
        self.jid = jid
        self.especialidade = especialidade
        self.turno = turno

    def get_medico(self):
        return self.jid

    def get_especialidade(self):
        return self.especialidade

    def get_turno(self):
        return self.turno

    def __str__(self):
        return f' {self.jid} {self.especialidade} {self.turno}'