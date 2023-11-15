objetivos = []


def enviar_objetivo(objetivo):
    objetivos.append(objetivo)
    print(objetivos)
    return "Objetivo recebido com sucesso"


def listar_objetivos(seila):
    global objetivos
    return "Os objetivos são: " + str(objetivos)



