import time
from flask import Flask, render_template, request, jsonify, send_file, Response
import openai
import pyttsx3
import json
import os
import pyfirmata2
import speech_recognition as sr
import PyPDF2

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

# Access the values and store them in separate variables
model = json_data[0]["model"]
api_key = json_data[0]["api_key"]
falar_texto = json_data[0]["assistente_falante"]
voz_pergunta = json_data[0]["voz_pergunta"]
voz_resposta = json_data[0]["voz_resposta"]
arduinoPorta = json_data[0]["arduino_porta"]
falar_pergunta = json_data[0]["falar_pergunta"]
falar_resposta = json_data[0]["falar_resposta"]

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
                with open(file_path, "w") as file:
                    json.dump(json_data, file, indent=4)
            except Exception as e:
                print("Deu ruim gravando", e)

        return json.dumps(resposta)
    except Exception as e:
        return "Deu ruim. Talvez o arduino esteja em outra porta? Ou está desconectado?: " + str(e)

def setar_pino(variaveis):
    global arduinoBoard

    resposta = variaveis
    try:
        if arduinoBoard == None:
            print("Configurando o Arduino na", arduinoPorta)
            arduinoBoard = pyfirmata2.Arduino(arduinoPorta)
        arduinoBoard.digital[variaveis["pino"]].write(variaveis["liga"])
        return json.dumps(resposta)
    except Exception as e:
        print("Falhou", str(e))
        return json.dumps({"error":"Deu ruim"})


def init_engine():
    engine = pyttsx3.init()
    return engine


def falando(resposta_t, voz):
    velocidade = 180

    engine = init_engine()

    engine.setProperty('rate', velocidade)
    voices = engine.getProperty('voices')
    for indice, vozes in enumerate(voices):  # listar vozes
        #print(indice, vozes.name) # listar as vozes instaladas
        pass
    engine.setProperty('voice', voices[voz].id)

    start = time.time()
    engine.say(resposta_t)
    print("Falando")

    engine.runAndWait()
    '''
    end = time.time()
    #print("Duracao", end - start)
    engine.stop()
    '''


def generate_answer(messages, modelo):
    try:
        response = openai.chat.completions.create(
            model=modelo,
            messages=messages,
            temperature=0.5,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "setar_porta",
                        "description": "Configurar o arduino em alguma porta",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "porta": {"type": "string", "description": "Porta do arduino"},
                            },
                            "required": ["porta"],
                        },
                    },
                },
                {
                    "type":"function",
                    "function": {
                        "name": "setar_pino",
                        "description": "Ligar um pino ou LED ou desligar um pino ou LED do arduino. Você deve receber um pedido para desligar ou ligar o LED ou pino e será informado o número do pino ou LED.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "pino": {"type": "integer", "description": "Pino ou LED do arduino"},
                                "liga": {"type": "boolean", "description": "Ligar ou desligar o LED ou pino"}
                            },
                            "required": ["pino", "liga"],
                        },
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "ler_arquivo",
                        "description": "Ler, resumir ou analisar um pdf.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "arquivo": {"type": "string", "description": "Nome do arquivo"},
                            },
                            "required": ["arquivo"],
                        },
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "listar_arquivos",
                        "description": "Listar os arquivos de uma pasta.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    }
                }
            ],
            tool_choice="auto",
        )
        first_response = response.choices[0].message
        print("\n###################################################")
        print("Primeira resposta:", first_response.content)
        #if first_response.content is None:
        #    first_response.content = ""
        #if first_response.function_call is None:
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

UPLOAD_FOLDER = ".\\docs"


@app.route('/')
def assistente_mil_grau():
    return render_template('index_chat.html')


@app.route('/assistente.html')
def assistente():
    return render_template('assistente.html', falar_texto=falar_texto)


@app.route('/avatar.html')
def avatar():
    return render_template('avatar.html', image_file=image_file)


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
        falando(pergunta, voz_pergunta)
        #pergunta_thread = threading.Thread(target=thread_falar, args=(pergunta, voz_pergunta))
        #pergunta_thread.start()
    response = generate_answer(data["userText"], model)

    if falar_texto and falar_pergunta:
        pass #pergunta_thread.join()
    try:
        resposta = response.choices[0].message.content
    except Exception as e:
        resposta = """
        Problemas Técnicos! Tente de novo ou faça uma gambiarra boa! Não esqueça de colocar sua Chave da OpenAI no arquivo "config_img.json"!\n\n Resposta:
        """ + str(response) + "!! \n\nErro: " + str(e)

    return resposta

@app.route('/falar', methods=['POST'])
def falar():
    global image_file
    texto = request.get_json()
    if falar_texto and falar_resposta:
        image_file = "01_chatbot_feliz.gif"
        update_image()

        falando(texto["texto"], voz_resposta)

        #falar_thread = threading.Thread(target=thread_falar, args=(texto["texto"], voz_resposta))
        #falar_thread.start()

        #while falar_thread.is_alive():
            #update_image()
        #    time.sleep(0.18)
            #print("falando")
        print("Falou")
        image_file = "02_chatbot_falando.gif"
        update_image()
    return {"ok": "ok"}


def salvar_config():
    global file_path

    def is_file_open(file_path):
        try:
            with open(file_path, 'r'):
                return False  # The file is not open
        except IOError:
            return True  # The file is open

    if is_file_open(file_path):
        print(f'The file "{file_path}" is open by another process.')
    else:
        print(f'The file "{file_path}" is not open.')

    # Save the updated JSON data back to the file
    try:
        with open(file_path, "w") as file_config:
            json.dump(json_data, file_config, indent=4)

        #file_voz = open('config_img.json', 'w')
        #json.dump(json_data, file_voz, indent=4)
        #file_voz.close()

    except Exception as e:
        print("Deu ruim gravando", e)
        #file_voz = open('config_img.json', 'r')
        #os.close(file_voz.fileno())


@app.route('/habilita_voz', methods=['GET'])
def habilita_voz():
    global falar_texto
    falar_texto = True if request.args.get('falar') == "true" else False

    json_data[0]["assistente_falante"] = falar_texto

    salvar_config()
    #salvar_thread = threading.Thread(target=salvar_config(), args=())
    #salvar_thread.start()
    #salvar_thread.join()

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
        print("Pressione o botão e fale...")
        audio = recognizer.listen(source)
    try:
        # Use a biblioteca de reconhecimento de voz para converter o áudio em texto
        text = recognizer.recognize_google(audio, language="pt-BR")
        print("Texto reconhecido: " + text)
    except sr.UnknownValueError:
        print("Não foi possível entender o áudio")
    except sr.RequestError as e:
        print("Erro na solicitação: {0}".format(e))
    return {"texto": text}


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

    return Response(status=204) #jsonify({"ok":"ok"}) #f'File {file.filename} uploaded successfully.'


def ler_arquivo(variaveis, max_paginas=5):
    arquivo = variaveis["arquivo"]

    filename_resumo = os.path.join(UPLOAD_FOLDER, arquivo)
    reader = PyPDF2.PdfReader(filename_resumo)
    #print("TEXTO DO ARQUIVO >>>>")
    texto_completo = ""
    total_paginas = len(reader.pages)
    if total_paginas > max_paginas:
        total_paginas = max_paginas
    for i in range(total_paginas):
        current_page = reader.pages[i]
        #print("===================")
        #print("Content on page:" + str(i + 1))
        #print("===================")
        #print(current_page.extract_text())
        texto_completo += "=================== Content on page:" + str(i + 1) + "===================\n" + current_page.extract_text()
    #print("<<<<<<<< FIM DO TEXTO")
    return texto_completo


def listar_arquivos(variaveis, pasta="docs"):
    pasta = "./" + pasta
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


if __name__ == '__main__':
    app.run(debug=True)
