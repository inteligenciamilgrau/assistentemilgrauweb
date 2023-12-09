const chatInput = document.querySelector("#chat-input");
const sendButton = document.querySelector("#send-btn");
const chatContainer = document.querySelector(".chat-container");
const deleteButton = document.querySelector("#delete-btn");
const recordButton = document.querySelector("#record-btn");

let userText = null;
let userHistory = [];

const defaultText = () => {

  chatContainer.innerHTML = `<div class="default-text">
  <p>Assistente Mil Grau</p>
</div>`;

  userHistory = [{ role: "system", content: "Seu nome é Assistente Mil Grau. Você tem 0 ouros."}];

  chatInput.disabled = false;

};

const createChatElement = (content, className) => {
  // Create new div and apply chat, specified class and set html content of div
  const chatDiv = document.createElement("div");
  chatDiv.classList.add("chat", className);
  chatDiv.innerHTML = content;
  return chatDiv; // Return the created chat div
};

const getChatResponse = async (incomingChatDiv) => {
  const pElement = document.createElement("p");

  var imagem = false;
  if (userText.startsWith("/img ")) {
        // Se sim, imprime "img" no console
        console.log("chegou img");
        imagem = true

        // Encontre a descrição da pergunta # a pergunta termina com ";"
        const descricaoRegex = /\/img\s(.*?)(?:;|\[)/;
        const descricaoMatch = descricaoRegex.exec(userText);
        const instrucao = descricaoMatch ? descricaoMatch[1].trim() : '';

        const nomesImagensRegex = /\[([^]+)]/;
        const nomesImagensMatch = userText.match(nomesImagensRegex);
        const imagens = nomesImagensMatch ? nomesImagensMatch[1].split(',').map(nome => nome.trim()) : [];

        //var instrucao = "Quantos animais tem mas imagens?"
        //var imagens = "https://www.ufmt.br/ocs/images/phocagallery/galeria2/thumbs/phoca_thumb_l_image03_grd.png,D:\\videos\\YouTube Tutoriais\\2023-IMG\\bob-editor\\87 - Yolo V8 Train\\_5a26e70e-abb2-4614-bc45-c65b748c6a0e.jfif"

        await ($.ajax({
            type: 'POST',
            url: '/imagens_multiplas',
            contentType: 'application/json',
            data: JSON.stringify({ instrucao: instrucao, imagens: imagens }),
            success: function(response_gpt) {
                response = response_gpt
                console.log(response_gpt)

                if(ativa_falar){
                    falar_texto(response);
                }

                // Escreve letra por letra no chat
                addWord(response, pElement);
            }
        }));

    } else {
        // Se não, imprime o texto original no console
        console.log(userText);
    }

  if(imagem){

  }else{
      userHistory.push({role: "user", content: userText});

      try {
        response = ""
        await ($.ajax({
            type: 'POST',
            url: '/enviar',
            contentType: 'application/json',
            data: JSON.stringify({ userText: userHistory }),
            success: function(response_gpt) {
                response = response_gpt
            }
        }));

        // para respostas do jogo da velha
        var regex = /{[^}]*}/;
        var correspondencias = response.match(regex);

        // Verifique se houve correspondência
        if (correspondencias) {
            // A primeira correspondência na string é o JSON
            var jsonEncontrado = correspondencias[0];

            // Remova qualquer texto antes ou depois do JSON
            jsonEncontrado = jsonEncontrado.replace(/.*{/,'{');
            //console.log("Encontrei", jsonEncontrado)

            // Analise o JSON
            try {
                //var response = JSON.parse(jsonEncontrado);
                var message = {
                    jogada: jsonEncontrado // Function name to call in Child 1
                };
                // jogar no jogo da velha
                parent.postMessage(message, "*");
            } catch (erro) {
                console.error('Erro ao analisar o JSON:', erro);
            }
        }

        if(ativa_falar){
            falar_texto(response);
        }

        // Escreve letra por letra no chat
        addWord(response, pElement);

        userHistory.push({role: "assistant", content: response});

      } catch (error) {
        // Add error class to the paragraph element and set error text
        pElement.classList.add("error");
        pElement.textContent =
          "Deu ruim no assistente! Tenta de novo!";
      }
  }


  // Remove the typing animation, append the paragraph element and save the chats to local storage
  incomingChatDiv.querySelector(".typing-animation").remove();
  incomingChatDiv.querySelector(".chat-details").appendChild(pElement);

  if (document.querySelectorAll(".chat-container .outgoing").length >= 1000) {
    chatInput.disabled = true;

    let html = `<div class="chat-content">
                    <div class="chat-details">
                        <img src="static/img/chatbot.png" alt="chatbot-img">
                        <p class='error'>Chegou ao limite de texto (<a href='#' onclick=\"document.querySelector('#delete-btn').click()\">Limpar</a>)</p>
                    </div>
                    <span onclick="copyResponse(this)" class="material-symbols-rounded">content_copy</span>
                </div>`;
  let incomingChatDiv = createChatElement(html, "incoming");
  chatContainer.appendChild(incomingChatDiv);

  }

  chatContainer.scrollTo(0, chatContainer.scrollHeight);
};

// Function to add words word by word
function addWord(response_add, pElement) {
    let wordIndex = 0;
    const words = response_add.split(' ');
    var delay_palavras = 50
    if(ativa_falar){
        delay_palavras = 300
    }
    function displayNextWord() {
        if (wordIndex < words.length) {
            pElement.textContent += words[wordIndex] + ' ';
            wordIndex++;
            setTimeout(displayNextWord, delay_palavras); // Adjust the delay (in milliseconds) as needed
        }
    }

    displayNextWord();
}

function falar_texto(response){
    $.ajax({
            type: 'POST',
            url: '/falar',
            contentType: 'application/json',
            data: JSON.stringify({ texto: response }),
            success: function(response_gpt) {
                //response = response_gpt
            }
        })
}

const copyResponse = (copyBtn) => {
  // Copy the text content of the response to the clipboard
  const reponseTextElement = copyBtn.parentElement.querySelector("p");
  navigator.clipboard.writeText(reponseTextElement.textContent);
  copyBtn.textContent = "done";
  setTimeout(() => (copyBtn.textContent = "content_copy"), 1000);
};

const showTypingAnimation = () => {
  // Display the typing animation and call the getChatResponse function
  const html = `<div class="chat-content">
                    <div class="chat-details">
                        <img src="static/img/chatbot.png" alt="chatbot-img">
                        <div class="typing-animation">
                            <div class="typing-dot" style="--delay: 0.2s"></div>
                            <div class="typing-dot" style="--delay: 0.3s"></div>
                            <div class="typing-dot" style="--delay: 0.4s"></div>
                        </div>
                    </div>
                    <span onclick="copyResponse(this)" class="material-symbols-rounded">content_copy</span>
                </div>`;
  // Create an incoming chat div with typing animation and append it to chat container
  const incomingChatDiv = createChatElement(html, "incoming");
  chatContainer.appendChild(incomingChatDiv);
  chatContainer.scrollTo(0, chatContainer.scrollHeight);
  getChatResponse(incomingChatDiv);
};

const handleOutgoingChat = () => {
  userText = chatInput.value.trim(); // Get chatInput value and remove extra spaces
  if (!userText) return; // If chatInput is empty return from here

  // Clear the input field and reset its height
  chatInput.value = "";

  const html = `<div class="chat-content">
                    <div class="chat-details">
                        <img src="static/img/user.png" alt="user-img">
                        <p>${userText}</p>
                    </div>
                </div>`;

  // Create an outgoing chat div with user's message and append it to chat container
  const outgoingChatDiv = createChatElement(html, "outgoing");
  chatContainer.querySelector(".default-text")?.remove();
  chatContainer.appendChild(outgoingChatDiv);
  chatContainer.scrollTo(0, chatContainer.scrollHeight);
  setTimeout(showTypingAnimation, 500);
};

deleteButton.addEventListener("click", () => {
  // Remove the chats from local storage and call loadDataFromLocalstorage function
  if (confirm("Apagar tudo?")) {
    defaultText();
  }
});

const initialInputHeight = chatInput.scrollHeight;

chatInput.addEventListener("input", () => {
  // Adjust the height of the input field dynamically based on its content
  chatInput.style.height = `${initialInputHeight}px`;
  chatInput.style.height = `${chatInput.scrollHeight}px`;
});

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleOutgoingChat();
  }
});

defaultText();
sendButton.addEventListener("click", handleOutgoingChat);

// Obtenha a referência à checkbox usando o id
var minhaCheckbox = document.getElementById("minhaCheckbox");

/* Verifique se a checkbox está marcada
if (minhaCheckbox.checked) {
    console.log("A checkbox está marcada.");
} else {
    console.log("A checkbox não está marcada.");
}
*/
var ativa_falar = document.getElementById('minhaCheckbox').checked

// Adicione um ouvinte de evento para detectar alterações na checkbox
minhaCheckbox.addEventListener("change", function() {
    if (minhaCheckbox.checked) {
        ativa_falar = true
    } else {
        ativa_falar = false
    }

    fetch('/habilita_voz?falar=' + ativa_falar, {
      method: 'GET', // This is the default, so you can omit it.
      headers: {
        'Content-Type': 'application/json', // Set the content type if needed.
        // You can add other headers here as needed.
      },
      // You can add additional options like credentials, mode, etc.
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json(); // Parse the response as JSON
    })
    .catch(error => {
      // Handle errors here
      console.error('Fetch error:', error);
    });
});

recordButton.addEventListener("click", function() {
    var texto = "";
    try{
        $.ajax({
        type: 'GET',
        url: '/gravar',
        contentType: 'application/json',
        data: JSON.stringify({ userText: userHistory }),
        success: function(response) {

            chatInput.value = response["texto"];
            handleOutgoingChat();
        }
    });
            }
           catch (error) {
                // Add error class to the paragraph element and set error text
                console.log("Deu ruim no assistente! Tenta de novo!" + error);
              }
    // This code will run when the button is clicked

    // You can replace the alert with any code you want to execute.
});

function jogar_com_chat(dados){
    var texto_jogada = 'Jogo da velha. Sua jogada, você é o "' + dados["jogador_atual"] +
    '" e o tabuleiro está assim: ' + dados["tabuleiro"] +
    '. Somente responda sua jogada no formato JSON como nos exemplos: {"jogada": 2} ou {"jogada": 7}';
    chatInput.value = ((dados["vencedor"] === "X" || dados["vencedor"] === "O") ? "Vencedor: " + dados["vencedor"] : texto_jogada)
    handleOutgoingChat();
    }

