#Classe para a comunicação de dados médicos de um paciente
from symbol import and_expr


class DadosPaciente:
    def __init__(self,jid,especialidade,bpm,bf,temperatura,grauPrioridade):
        self.jid = jid
        self.especialidade = especialidade
        self.bpm = bpm
        self.bf = bf
        self.temperatura = temperatura
        self.grauPrioridade = grauPrioridade
        

    def get_jid(self):
        return self.jid

    def get_especialidade(self):
        return self.especialidade

    def get_bpm(self):
        return self.bpm

    def get_bf(self):
        return self.bf

    def get_temp(self):
        return self.temperatura

    def get_grau(self):
        return self.grauPrioridade


    def set_jid(self,jid):
        self.jid = jid

    def set_especialidade(self,especialidade):
        self.especialidade = especialidade

    def set_bpm(self,bpm):
        self.bpm = bpm

    def set_bf(self,bf):
        self.bf = bf

    def set_temp(self,temperatura):
        self.temperatura = temperatura

    def set_grau(self,grauPrioridade):
        self.grauPrioridade = grauPrioridade


    def __eq__(self, other):
        if not isinstance(other, DadosPaciente):
            return False
        return (
                self.jid == other.jid and
                self.especialidade == other.especialidade and
                self.bpm == other.bpm and
                self.bf == other.bf and
                self.temperatura == other.temperatura and
                self.grauPrioridade == other.grauPrioridade
        )
