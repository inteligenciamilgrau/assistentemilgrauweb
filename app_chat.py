import time
from flask import Flask, render_template, request, jsonify
import openai
import pyttsx3
import threading
import json
import os
import speech_recognition as sr

app = Flask(__name__)

recognizer = sr.Recognizer()

# Check if the config.json file exists
if os.path.exists('config.json'):
    # Read the JSON data from the existing file
    with open('config.json', 'r') as file:
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
            "falar_pergunta": False,
            "falar_resposta": True
        }
    ]

    with open('config.json', 'w') as file:
        json.dump(initial_data, file, indent=4)

    # Set the initial data to the json_data variable
    json_data = initial_data

# Access the values and store them in separate variables
model = json_data[0]["model"]
api_key = json_data[0]["api_key"]
falar_texto = json_data[0]["assistente_falante"]
voz_pergunta = json_data[0]["voz_pergunta"]
voz_resposta = json_data[0]["voz_resposta"]
falar_pergunta = json_data[0]["falar_pergunta"]
falar_resposta = json_data[0]["falar_resposta"]

# Now you have two variables, model and api_key, containing the values from the JSON
print("Model:", model)
print("Falar Texto:", falar_texto)

openai.api_key = api_key

if api_key == "sua-api-key-openai":
    print("Coloque a sua chave no arquivo config.json")


image_file = "01_chatbot_feliz.gif"


def thread_falar(resposta_t, voz):
    velocidade = 180
    engine = pyttsx3.init()
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
    end = time.time()
    print("Duracao", end - start)


def generate_answer(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=1.0,
        )
        return response
    except Exception as e:
        print("Erro", e)
        return e


tabuleiro = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
jogador_atual = "X"
vencedor = None
jogadas = 0


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
        pergunta_thread = threading.Thread(target=thread_falar, args=(pergunta, voz_pergunta))
        pergunta_thread.start()
    response = generate_answer(data["userText"])

    if falar_texto and falar_pergunta:
        pergunta_thread.join()
    try:
        resposta = response.choices[0].message.content
    except Exception as e:
        resposta = """
        Problemas Técnicos! Tente de novo ou faça uma gambiarra boa! Não esqueça de colocar sua Chave da OpenAI no arquivo Config!\n\n Resposta:
        """ + str(response) + "!! \n\nErro: " + str(e)

    return resposta

@app.route('/falar', methods=['POST'])
def falar():
    global image_file
    texto = request.get_json()
    if falar_texto and falar_resposta:
        image_file = "01_chatbot_feliz.gif"
        update_image()

        falar_thread = threading.Thread(target=thread_falar, args=(texto["texto"], voz_resposta))
        falar_thread.start()

        while falar_thread.is_alive():
            #update_image()
            time.sleep(0.18)
            print("falando")
        image_file = "02_chatbot_falando.gif"
        update_image()
    return {"ok": "ok"}

@app.route('/habilita_voz', methods=['GET'])
def habilita_voz():
    global falar_texto
    falar_texto = bool(request.args.get('falar'))

    json_data[0]["assistente_falante"] = falar_texto

    # Save the updated JSON data back to the file
    try:
        with open("config.json", "w") as file:
            json.dump(json_data, file, indent=4)
    except Exception as e:
        print("Deu ruim gravando", e)

    return {"ok":"Ok"}


@app.route('/about')
def about():
    return render_template('about.html')


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


if __name__ == '__main__':
    app.run(debug=True)
