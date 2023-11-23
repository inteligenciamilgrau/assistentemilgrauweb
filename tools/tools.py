import json

with open('./tools/tools.json', 'r') as file:
    tools = json.load(file)['tools']

objetivos = []

def listar_comandos(nt):
    return str([tool['function']['description'] for tool in tools])

def enviar_objetivo(objetivo):
    objetivos.append(objetivo)
    print(objetivos)
    return "Objetivo recebido com sucesso"


def listar_objetivos(seila):
    global objetivos
    return "Os objetivos são: " + str(objetivos)


def preco_das_coisas(informacoes):
    objeto = informacoes["objeto"]
    preco = informacoes["preco"]
    print("preços: ", objeto, preco)
    return "Preço recebido: " + objeto + " custa " + str(preco)


def vender_pao(info):
    print("Vendendo pao!")
    return "Pao vendido"
