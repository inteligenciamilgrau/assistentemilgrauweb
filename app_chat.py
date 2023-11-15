from flask import Flask, render_template, request, jsonify, send_file, Response
import openai
import pyttsx3
import json
import os
import pyfirmata2
import speech_recognition as sr
import PyPDF2
import threading
import time
import base64
import requests
from tools.tools import *

app = Flask(__name__)

recognizer = sr.Recognizer()

file_path = 'config_img.json'  # Replace with the path to your file

# Check if the config_img.json file exists
if os.path.exists(file_path):
    # Read the JSON data from the existing file
    with open(file_path, 'r') as file:
        json_data = json.load(file)
else:
    # If the file doesn't exist, create it with specific content
    initial_data = [
        {
            "model": "gpt-3.5-turbo",
            "model_vision": "gpt-4-vision-preview",
            "api_key": "sua-api-key-openai",
            "assistente_falante": False,
            "voz_pergunta": 0,
            "voz_resposta": 1,
            "arduino_porta": "COM1",
            "falar_pergunta": False,
            "falar_resposta": True
        }
    ]

    with open(file_path, 'w') as file:
        json.dump(initial_data, file, indent=4)

    # Set the initial data to the json_data variable
    json_data = initial_data

with open('./tools/tools.json', 'r') as file:
    tools = json.load(file)

# Access the values and store them in separate variables
model = json_data[0]["model"]
model_vision = json_data[0]["model_vision"]
api_key = json_data[0]["api_key"]
falar_texto = json_data[0]["assistente_falante"]
voz_pergunta = json_data[0]["voz_pergunta"]
voz_resposta = json_data[0]["voz_resposta"]
arduinoPorta = json_data[0]["arduino_porta"]
falar_pergunta = json_data[0]["falar_pergunta"]
falar_resposta = json_data[0]["falar_resposta"]
camera_pic_url = "http://seu_ip_aqui_oh/capture"

arduinoBoard = None
variaveis_locais = locals()

# Now you have two variables, model and api_key, containing the values from the JSON
print("Model:", model)
print("Falar Texto:", falar_texto)

openai.api_key = api_key

if api_key == "sua-api-key-openai":
    print("Coloque a sua chave no arquivo config_img.json")

image_file = "01_chatbot_feliz.gif"


def setar_porta(porta):
    global arduinoBoard

    resposta = porta["porta"]
    try:
        arduinoBoard = pyfirmata2.Arduino(porta["porta"])

        if not porta["porta"] == json_data[0]["arduino_porta"]:
            json_data[0]["arduino_porta"] = porta["porta"]
            try:
                with open(os.path.join(ACTUAL_FOLDER + file_path), "w") as file_porta:
                    json.dump(json_data, file_porta, indent=4)
            except Exception as e:
                print("Deu ruim gravando", e)

        return json.dumps(resposta)
    except Exception as e:
        return "Deu ruim. Talvez o arduino esteja em outra porta? Ou está desconectado?: " + str(e)


def setar_pino(variaveis):
    global arduinoBoard

    resposta = variaveis
    try:
        if arduinoBoard is None:
            print("Configurando o Arduino na", arduinoPorta)
            arduinoBoard = pyfirmata2.Arduino(arduinoPorta)
        arduinoBoard.digital[variaveis["pino"]].write(variaveis["liga"])
        return json.dumps(resposta)
    except Exception as e:
        print("Falhou", str(e))
        return json.dumps({"error": "Deu ruim"})


def falando(resposta_t, voz):
    velocidade = 180

    engine = pyttsx3.init()

    engine.setProperty('rate', velocidade)
    voices = engine.getProperty('voices')
    for indice, vozes in enumerate(voices):  # listar vozes
        #print(indice, vozes.name)  # listar as vozes instaladas
        pass
    engine.setProperty('voice', voices[voz].id)

    # start = time.time()
    engine.say(resposta_t)
    print("Falando")

    engine.runAndWait()
    '''
    end = time.time()
    #print("Duracao", end - start)
    engine.stop()
    '''


def generate_answer(messages, modelo):
    print("Perguntando ao modelo", modelo)
    try:
        response = openai.chat.completions.create(
            model=modelo,
            messages=messages,
            temperature=0.5,
            tools=tools["tools"],
            tool_choice="auto",
        )
        first_response = response.choices[0].message
        print("\n###################################################")
        print("Primeira resposta:", first_response.content)
        # if first_response.content is None:
        #    first_response.content = ""
        # if first_response.function_call is None:
        #    del first_response.function_call

        tool_calls = first_response.tool_calls

        # Passo 2, verifica se o modelo quer chamar uma funcao
        if tool_calls:

            def listar_funcoes():
                return {nome: objeto for nome, objeto in variaveis_locais.items() if callable(objeto)}

            available_functions = listar_funcoes()

            messages.append(first_response)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)

                print("************************")
                print("Detectou uma função", function_name, function_args)
                print("************************")

                function_response = function_to_call(function_args)

                print("function_response", function_response)

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )

            if function_name == "analisar_imagem":
                response.choices[0].message.content = "COMANDO: " + function_response
            else:
                second_response = openai.chat.completions.create(
                    model=modelo,
                    messages=messages,
                )

                print("Segunda Resposta:", second_response.choices[0].message.content)
                response = second_response
                response.choices[0].message.content = "COMANDO: " + response.choices[0].message.content

            return response
        return response
    except Exception as e:
        print("Erro de excessão:", e)
        return e


tabuleiro = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
jogador_atual = "X"
vencedor = None
jogadas = 0

ACTUAL_FOLDER = os.getcwd()
UPLOAD_FOLDER = ACTUAL_FOLDER + "\\docs"


@app.route('/')
def assistente_mil_grau():
    return render_template('index_chat.html')


@app.route('/assistente.html')
def assistente():
    return render_template('assistente.html', falar_texto=falar_texto)


@app.route('/avatar.html')
def avatar():
    return render_template('avatar.html', image_file=image_file)


@app.route('/stream.html')
def stream():
    return render_template('stream.html')

@app.route('/update_image', methods=['GET', 'POST'])
def update_image():
    # Update the image file variable based on some condition
    # In this example, we toggle between two images
    global image_file
    image_file = "02_chatbot_falando.gif" if image_file == "01_chatbot_feliz.gif" else "01_chatbot_feliz.gif"

    # Return the new image file path
    return jsonify(image_file)


@app.route('/actual_image_file', methods=['GET', 'POST'])
def actual_image_file():
    # Return the new image file path
    return jsonify({"img": image_file})


@app.route('/enviar', methods=['POST'])
def enviar():
    global image_file

    data = request.get_json()

    if falar_texto and falar_pergunta:
        pergunta = data["userText"][-1]["content"]
        #falando(pergunta, voz_pergunta)
        pergunta_thread = threading.Thread(target=falando, args=(pergunta, voz_pergunta))
        pergunta_thread.start()
    response = generate_answer(data["userText"], model)

    if falar_texto and falar_pergunta:
        pergunta_thread.join()
    try:
        resposta = response.choices[0].message.content
    except Exception as e:
        resposta = """
        Problemas Técnicos! Tente de novo ou faça uma gambiarra boa! Não esqueça de colocar\
         sua Chave da OpenAI no arquivo "config_img.json"!\n\n Resposta:
        """ + str(response) + "!! \n\nErro: " + str(e)

    return resposta


@app.route('/falar', methods=['POST'])
def falar():
    global image_file
    texto = request.get_json()
    if falar_texto and falar_resposta:
        image_file = "01_chatbot_feliz.gif"
        update_image()

        # falando(texto["texto"], voz_resposta)

        falar_thread = threading.Thread(target=falando, args=(texto["texto"], voz_resposta))
        falar_thread.start()

        while falar_thread.is_alive():
            update_image()
            time.sleep(0.18)
        # print("falando")
        print("Falou")
        image_file = "02_chatbot_falando.gif"
        update_image()
    return {"ok": "ok"}


def salvar_config():
    global file_path

    diretorio_atual = ACTUAL_FOLDER
    caminho_completo = os.path.join(diretorio_atual, file_path)

    def is_file_open(caminho_completo_file):
        try:
            with open(caminho_completo_file, 'r'):
                return False  # The file is not open
        except IOError:
            return True  # The file is open

    if is_file_open(caminho_completo):
        print(f'The file "{file_path}" is open by another process.')
    else:
        print(f'The file "{file_path}" is not open.')

    # Save the updated JSON data back to the file
    try:
        with open(caminho_completo, "w") as file_config:
            json.dump(json_data, file_config, indent=4)

        # file_voz = open('config_img.json', 'w')
        # json.dump(json_data, file_voz, indent=4)
        # file_voz.close()

    except Exception as e:
        print("Deu ruim gravando", e)
        # file_voz = open('config_img.json', 'r')
        # os.close(file_voz.fileno())


@app.route('/habilita_voz', methods=['GET'])
def habilita_voz():
    global falar_texto
    falar_texto = True if request.args.get('falar') == "true" else False

    json_data[0]["assistente_falante"] = falar_texto

    salvar_config()
    # salvar_thread = threading.Thread(target=salvar_config(), args=())
    # salvar_thread.start()
    # salvar_thread.join()

    return {"Falar": falar_texto}


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/arduino')
def arduino():
    return render_template('arduino.html')


@app.route('/gravar')
def gravar():
    with sr.Microphone() as source:
        print("Pode falar, já estou te ouvindo...")
        audio = recognizer.listen(source)
    try:
        print("Enviando...")
        # Use a biblioteca de reconhecimento de voz para converter o áudio em texto
        text = recognizer.recognize_google(audio, language="pt-BR")
        print("Texto reconhecido: " + text)
        return {"texto": text}
    except sr.UnknownValueError:
        print("Não foi possível entender o áudio")
    except sr.RequestError as e:
        print("Erro na solicitação: {0}".format(e))
        return {"texto": e}
    return {"texto": "Não detectou nada"}


@app.route('/jogo.html')
def jogo():
    return render_template('jogo.html', tabuleiro=tabuleiro, jogador_atual=jogador_atual, vencedor=vencedor)


@app.route('/atualizar_jogada', methods=['POST'])
def atualizar_jogada():
    global jogador_atual, vencedor, jogadas, tabuleiro
    data = request.get_json()
    posicao = data['posicao'] - 1
    jogadas += 1

    if not tabuleiro[posicao] in ["X", "O"] and not vencedor:
        tabuleiro[posicao] = jogador_atual

        if verificar_vencedor(jogador_atual):
            vencedor = jogador_atual

        elif jogadas >= 9:
            vencedor = "Empate"

        jogador_atual = "X" if jogador_atual == "O" else "O"

        return jsonify({'tabuleiro': tabuleiro, 'vencedor': vencedor, 'jogador_atual': jogador_atual})

    tabuleiro = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    jogador_atual = "X"
    vencedor = None
    jogadas = 0

    return jsonify({'tabuleiro': tabuleiro, 'vencedor': vencedor, 'jogador_atual': jogador_atual})


@app.route('/pegar_dados', methods=['POST'])
def pegar_dados():
    return jsonify({'tabuleiro': tabuleiro, 'vencedor': vencedor, 'jogador_atual': jogador_atual})


def verificar_vencedor(jogador):
    # Lógica para verificar se um jogador venceu
    return ((tabuleiro[0] == tabuleiro[1] == tabuleiro[2] == jogador) or
            (tabuleiro[3] == tabuleiro[4] == tabuleiro[5] == jogador) or
            (tabuleiro[6] == tabuleiro[7] == tabuleiro[8] == jogador) or
            (tabuleiro[0] == tabuleiro[3] == tabuleiro[6] == jogador) or
            (tabuleiro[1] == tabuleiro[4] == tabuleiro[7] == jogador) or
            (tabuleiro[2] == tabuleiro[5] == tabuleiro[8] == jogador) or
            (tabuleiro[0] == tabuleiro[4] == tabuleiro[8] == jogador) or
            (tabuleiro[2] == tabuleiro[4] == tabuleiro[6] == jogador))


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'
    filen = request.files['file']
    if filen:
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        filename = os.path.join(UPLOAD_FOLDER, filen.filename)
        filen.save(filename)

    return Response(status=204)  # jsonify({"ok":"ok"}) #f'File {file.filename} uploaded successfully.'


def ler_arquivo(variaveis, max_paginas=5):
    arquivo = variaveis["arquivo"]

    filename_resumo = os.path.join(UPLOAD_FOLDER, arquivo)
    reader = PyPDF2.PdfReader(filename_resumo)
    # print("TEXTO DO ARQUIVO >>>>")
    texto_completo = ""
    total_paginas = len(reader.pages)
    if total_paginas > max_paginas:
        total_paginas = max_paginas
    for i in range(total_paginas):
        current_page = reader.pages[i]
        # print("===================")
        # print("Content on page:" + str(i + 1))
        # print("===================")
        # print(current_page.extract_text())
        texto_completo += "=================== Content on page:" + str(
            i + 1) + "===================\n" + current_page.extract_text()
    # print("<<<<<<<< FIM DO TEXTO")
    return texto_completo


def listar_arquivos(variaveis, pasta=UPLOAD_FOLDER):
    # pasta = "./" + pasta
    if os.path.exists(pasta):
        if os.path.isdir(pasta):
            files = [f for f in os.listdir(pasta) if os.path.isfile(os.path.join(pasta, f))]
            return ', '.join(files)
        else:
            return "Nenhum arquivo encontrado."  # Not a folder
    else:
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        return "Nenhum arquivo encontrado."


@app.route('/view/<filename>')
def view_pdf(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))


@app.route('/camera_url', methods=['GET'])
def camera_url():
    global camera_pic_url

    camera_pic_url = str(request.args.get("camera")).replace(":81/stream", "/capture")
    print("A nova url da camera é", camera_pic_url)

    return Response(status=204)  # jsonify({"ok":"ok"}) #f'File {file.filename} uploaded successfully.'


def analisar_imagem(variaveis):
    def encode_image(image_path_encode):
        if image_path_encode.startswith("http"):
            return base64.b64encode(requests.get(image_path_encode).content).decode('utf-8')
        else:
            with open(image_path_encode, "rb") as image_file_web:
                return base64.b64encode(image_file_web.read()).decode('utf-8')

    # image_path = "http://ip_intelbras/onvif/snapshot.jpg"
    # image_path = "http://ip_esp32/capture"
    image_path = camera_pic_url
    print("image_path", image_path)
    base64_image = encode_image(image_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "O que tem nessa imagem?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }
    resposta = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return resposta.json()['choices'][0]["message"]["content"]


mover = []
destino = "none"
procurando = False

def send_movement(movement):
    url = "http://127.0.0.1:5000/move_player"
    params = {"direction": '["' + movement + '"]'}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises HTTPError for bad responses
        #print(f"Movement '{movement}' sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending movement: {e}")


def dijkstra(graph, start, goal):
    priority_queue = [(0, start, [])]
    visited = set()

    while priority_queue:
        priority_queue.sort()
        (cost, current, path) = priority_queue.pop(0)

        if current in visited:
            continue

        visited.add(current)

        if current == goal:
            return path

        for neighbor, (weight, direction) in graph[current].items():
            priority_queue.append((cost + weight, neighbor, path + [direction]))

    return []

def create_graph(map_data):
    rows, cols = len(map_data), len(map_data[0])
    graph = {(i, j): {} for i in range(rows) for j in range(cols)}

    for i in range(rows):
        for j in range(cols):
            if map_data[i][j] == 'B':
                continue

            for x, y, direction in [(i + 1, j, "Down"), (i - 1, j, "Up"), (i, j + 1, "Right"), (i, j - 1, "Left")]:
                if 0 <= x < rows and 0 <= y < cols and map_data[x][y] != 'B':
                    graph[(i, j)][(x, y)] = (1, direction)

    return graph

def encontrar_caminho(map_data, map_goal):
    start = None
    goal = None

    for i in range(len(map_data)):
        for j in range(len(map_data[0])):
            if map_data[i][j] == 'P':
                start = (i, j)
            elif map_data[i][j] == map_goal:
                goal = (i, j)

    if start is None or goal is None:
        #print("Invalid map: Start or Goal not found.")
        return ["parado"]

    graph = create_graph(map_data)
    shortest_path = dijkstra(graph, start, goal)

    if not shortest_path:
        #print("No path found.")
        return []
    else:
        #print("Shortest path:", str(shortest_path).replace(" ", "").replace("'", "\""))
        return shortest_path



@app.route('/rpg')
def rpg():
    return render_template('rpg.html')


# http://127.0.0.1:5000/move_player?direction=[%22R%22,%22R%22,%22R%22,%22D%22,%22D%22,%22D%22]
@app.route('/move_player', methods=['GET'])
def move_player():
    global mover
    mover = request.args.get('direction')

    #print("dir", json.loads(mover)[0])
    return 'Move command received'


#@app.route('/destino_player', methods=['GET'])
def destino_player(destiny):
    global destino, procurando
    #destino = request.args.get('destino')
    destino = destiny["destino"].lower()
    procurando = True
    return 'Recebi ' + str(destino) + " com sucesso"


@app.route('/update_tilemap', methods=['POST'])
def update_tilemap():
    global mover, destino, procurando
    data = request.get_json()
    tilemap = data.get('tilemap')#
    player_coord = (data.get('player_coord_x'), data.get('player_coord_y'))
    gold_coord = (data.get('gold_x'), data.get('gold_y'))

    def place_player_and_gold(tilemap, player_coord, gold_coord):
        # Convert coordinates to row and column indices
        player_col, player_row = player_coord
        gold_col, gold_row = gold_coord

        # Iterate through the tilemap and update player and gold positions
        for i in range(len(tilemap)):
            for j in range(len(tilemap[i])):
                if (i, j) == (player_row, player_col):
                    tilemap[i] = tilemap[i][:j] + 'P' + tilemap[i][j + 1:]
                elif (i, j) == (gold_row, gold_col):
                    tilemap[i] = tilemap[i][:j] + 'G' + tilemap[i][j + 1:]

        return tilemap

    movendo = []
    if not mover == []:
        movendo = mover
        mover = []

    updated_tilemap = place_player_and_gold(tilemap, player_coord, gold_coord)
    # Handle the direction and send it to the player
    tilemap_string = '\n'.join(updated_tilemap).replace("XP", "")

    updated_tilemap[-1] = updated_tilemap[-1].replace("XP", "")

    locais = {"casa": "H", "mercado": "M", "ouro": "G"}

    if destino in locais:
        letters_to_find = ['M', 'H', 'G']
        def find_letters_coordinates(tilemap, letters):
            coordinates = {letter: [] for letter in letters}

            for y, row in enumerate(tilemap):
                for x, char in enumerate(row):
                    if char in letters:
                        coordinates[char].append((x, y))

            return coordinates

        letters_coordinates = find_letters_coordinates(tilemap, letters_to_find)
        #print("coords", player_coord, gold_coord, letters_coordinates)
        if not letters_coordinates[locais[destino]]:
            print("CONSEGUIU")
            destino = ""
            procurando = False
        if not destino == "":
            caminho = encontrar_caminho(updated_tilemap, locais[destino])
            if not caminho[0] == "parado":
                send_movement(caminho[0])


    #print("caminho", caminho[0])

    #time.sleep(1)

    #print("tilemap_string", "\n"+tilemap_string, "player_coord", player_coord, "gold_coord", gold_coord)
    return jsonify({'message': 'Tilemap updated successfully', 'move': movendo})


def realizar_objetivos(seila):
    global objetivos
    for objetivo in objetivos:
        print(objetivo["objetivo"])
        message = [{"role": "user", "content": objetivo["objetivo"]}]
        response = generate_answer(message, model)
        print(response.choices[0].message.content)
        while procurando:
            time.sleep(1)
            print("realizando")
    objetivos = []
    return "Objetivos realizados"


if __name__ == '__main__':
    app.run(debug=True)
