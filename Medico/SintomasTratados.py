#Classe para mandar a mensagem com os sintomas tratados ao Paciente doente

class SintomasTratados:
    def __init__(self, jid: str, sintomas_tratados: dict):
        self.jid = jid
        self.sintomas_tratados = sintomas_tratados

    def getJid(self):
        return self.jid

    def getSintomasTratados(self):
        return self.sintomas_tratados

    def __str__(self):
        return f' {self.jid} {self.sintomas_tratados}'