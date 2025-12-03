* Instale as bibliotecas:



pip install -r requirements.txt



ou



pip3 install -r requirements.txt



* Na pasta UTILS vá ate config.py e direcione o caminho até seu vídeo de teste em:



TEST\_VIDEO\_PATH = r"C:/Users/Meu Computador/Pictures/PROJETO GLOBO/teste11.mp4"



USE_WEBCAM = False


* Ainda em config.py adicione as credencias do seu banco de dados 



* Abra o terminal e rode o backend em:



uvicorn main:app --host 0.0.0.0 --port 8000

