import time
from flask import Flask, render_template, request, jsonify
import openai
import pyttsx3
import threading
import json
import os
try:
    import pyfirmata2
except:
    print("Instalar pyfirmata2 para usar arduino")

app = Flask(__name__)

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
            "arduino_porta": "COM1"
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
arduinoBoard = json_data[0]["arduino_porta"]

# Now you have two variables, model and api_key, containing the values from the JSON
print("Model:", model)
print("Falar Texto:", falar_texto)

openai.api_key = api_key

if api_key == "sua-api-key-openai":
    print("Coloque a sua chave no arquivo config.json")

image_file = "01_chatbot_feliz.png"


def setar_porta(porta):
    global arduinoBoard

    print("Setando porta")
    print("Dados", porta)
    resposta = {
        "porta": porta,
    }
    try:
        arduinoBoard = pyfirmata2.Arduino(porta)

        json_data[0]["arduino_porta"] = porta

        # Save the updated JSON data back to the file
        try:
            with open("config.json", "w") as file:
                json.dump(json_data, file, indent=4)
        except Exception as e:
            print("Deu ruim gravando", e)

        return json.dumps(resposta)
    except Exception as e:
        return "Deu ruim: " + str(e)

def setar_pino(pino, estado):
    print("Setando pino")
    print("Dados", pino, estado)
    resposta = {
        "pino": pino,
        "estado": estado,
    }
    try:
        arduinoBoard.digital[pino].write(estado)
        return json.dumps(resposta)
    except Exception as e:
        return "Deu ruim: " + str(e)

def thread_falar(resposta_t, voz):
    velocidade = 180
    engine = pyttsx3.init()
    engine.setProperty('rate', velocidade)
    voices = engine.getProperty('voices')
    for indice, vozes in enumerate(voices):  # listar vozes
        print(indice, vozes.name)
        pass
    engine.setProperty('voice', voices[voz].id)

    start = time.time()
    engine.say(resposta_t)
    print("Falando")
    engine.runAndWait()
    end = time.time()
    print("Duracao", end - start)

def generate_answer(messages, modelo):
    try:
        response = openai.ChatCompletion.create(
            model=modelo,
            messages=messages,
            temperature=1.0,
            functions=[
                {
                    "name": "setar_porta",
                    "description": "Configurar a porta do arduino",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "porta": {"type": "string", "description": "Porta do arduino"},
                        },
                        "required": ["porta"],
                    },
                },
                {
                    "name": "setar_pino",
                    "description": "Ligar ou desligar o estado de um pino do arduino",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pino": {"type": "integer", "description": "Pino do arduino"},
                            "estado": {"type": "boolean", "description": "true of false"}
                        },
                        "required": ["pino", "estado"],
                    },
                }
            ],
            function_call="auto",
        )
        first_response = response["choices"][0]["message"]
        print("\n###################################################")
        print("Primeira resposta:", first_response['content'])

        # Passo 2, verifica se o modelo quer chamar uma funcao
        if first_response.get("function_call"):
            function_name = first_response["function_call"]["name"]
            function_args = json.loads(first_response["function_call"]["arguments"])

            print("************************")
            print("Detectou uma função", function_name, function_args)
            print("************************")

            # Passo 3, chama a funcao
            # Detalhe: a resposta em JSON do modelo pode não ser um JSON valido
            if function_name == "setar_pino":
                function_response = setar_pino(
                    pino=function_args.get("pino"),
                    estado=function_args.get("estado"),
                )

                # Passo 4 - opcional , manda pro modelo a resposta da chamada de funcao
                messages.append(first_response)  # extend conversation with assistant's reply
                messages.append(
                    {
                        "role": "function",
                        "name": function_name,
                        "content": function_response,
                    }
                )
                second_response = openai.ChatCompletion.create(
                        model=modelo,
                        messages=messages
                    )
                print(second_response)
                print("Segunda Resposta:", second_response["choices"][0]["message"]['content'])
                response = second_response
                response["choices"][0]["message"]['content'] = "COMANDO: " + response["choices"][0]["message"][
                    'content']
            elif function_name == "setar_porta":
                function_response = setar_porta(
                    porta=function_args.get("porta"),
                )

                # Passo 4 - opcional , manda pro modelo a resposta da chamada de funcao
                messages.append(first_response)  # extend conversation with assistant's reply
                messages.append(
                    {
                        "role": "function",
                        "name": function_name,
                        "content": function_response,
                    }
                )
                second_response = openai.ChatCompletion.create(
                        model=modelo,
                        messages=messages
                    )
                print(second_response)
                print("Segunda Resposta:", second_response["choices"][0]["message"]['content'])
                response = second_response
                response["choices"][0]["message"]['content'] = "COMANDO: " + response["choices"][0]["message"][
                    'content']
            else:
                print("Nao achei a funcao pedida")
        return response
    except Exception as e:
        print("Erro de excessão:", e)
        return e

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
    image_file = "02_chatbot_falando.png" if image_file == "01_chatbot_feliz.png" else "01_chatbot_feliz.png"

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

    if falar_texto:
        pergunta = data["userText"][-1]["content"]
        pergunta_thread = threading.Thread(target=thread_falar, args=(pergunta, voz_pergunta))
        pergunta_thread.start()
    response = generate_answer(data["userText"], model)

    if falar_texto:
        pergunta_thread.join()
    try:
        resposta = response.choices[0].message.content
    except Exception as e:
        resposta = """
        Problemas Técnicos! Tente de novo ou faça uma gambiarra boa! Não esqueça de colocar sua Chave da OpenAI no arquivo Config!\n\n Resposta:
        """ + str(response) + "!! \n\nErro: " + str(e)

    if falar_texto:
        falar_thread = threading.Thread(target=thread_falar, args=(resposta[:resposta.find("Resposta:")], voz_resposta))
        falar_thread.start()

        while falar_thread.is_alive():
            update_image()
            time.sleep(0.18)
            print("falando")
        image_file = "02_chatbot_falando.png"
        update_image()

    return resposta


@app.route('/falar', methods=['GET'])
def falar():
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


if __name__ == '__main__':
    app.run(debug=True)
