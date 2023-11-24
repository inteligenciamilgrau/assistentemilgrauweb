from flask import Flask, render_template, request, jsonify, send_file, Response
import speech_recognition as sr
from tools.tools import *

app = Flask(__name__)

recognizer = sr.Recognizer()

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
    return enviando_pergunta(request.get_json())


@app.route('/falar', methods=['POST'])
def falar():
    assistente_fala_texto(request.get_json())
    return {"ok": "ok"}


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


@app.route('/view/<filename>')
def view_pdf(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))


@app.route('/camera_url', methods=['GET'])
def camera_url():
    camera_image_url = str(request.args.get("camera")).replace(":81/stream", "/capture")
    print("A nova url da camera é", camera_image_url)
    atualiza_camera_url(camera_image_url)

    return Response(status=204)  # jsonify({"ok":"ok"}) #f'File {file.filename} uploaded successfully.'


@app.route('/rpg')
def rpg():
    return render_template('rpg.html')


# http://127.0.0.1:5000/move_player?direction=[%22R%22,%22R%22,%22R%22,%22D%22,%22D%22,%22D%22]
@app.route('/move_player', methods=['GET'])
def move_player():
    mover_o_jogador(request.args.get('direction'))

    return 'Move command received'


@app.route('/update_tilemap', methods=['POST'])
def update_tilemap():
    data = request.get_json()
    movendo = atualiza_mapa(data)

    return jsonify({'message': 'Tilemap updated successfully', 'move': movendo})


@app.route('/grafico')
def grafico():
    # Render the HTML template and pass the image file to it
    return render_template('grafico.html', image_file='grafico.png')


if __name__ == '__main__':
    app.run(debug=True)
