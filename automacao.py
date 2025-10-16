import os
from dotenv import load_dotenv
import imaplib
import email
from email.header import decode_header
import requests

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

IMAP_SERVER = "imap-mail.outlook.com"

def verificar_novas_tarefas_asana():
    """
    Esta função se conecta ao Hotmail, procura por e-mails não lidos do Asana
    sobre novas tarefas e retorna uma lista com os nomes das tarefas encontradas.
    """
    print("Verificando novas tarefas do Asana...")
    tarefas_encontradas = [] # armazenando as tarefas encontradas em uma lista vazia
    
    try:
        iamp = imaplib.IMAP4_SSL(IMAP_SERVER)
        iamp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        iamp.select("inbox")
        
        status, messages = iamp.search(None, 'UNSEEN', 'FROM', '"notify@asana.com"', 'SUBJECT', '"assigned"')

        if status == "OK":
            email_ids = messages[0].split()
            print(f"Encontrado(s) {len(email_ids)} e-mail(s) do Asana não lido(s).")
            
            for email_id in email_ids:
                _, msg_data = iamp.fetch(email_id, "(RFC822)")
                
                msg = email.message_from_bytes(msg_data[0][1])

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            for line in body.splitlines():
                                if "foi atribuída a você:" in line:
                                    nome_tarefa = line.split("'")[1]
                                    tarefas_encontradas.append(nome_tarefa)
                                    print(f"Tarefa encontrada: '{nome_tarefa}'")
                                    break 
                            break
    
    except Exception as e:
        print(f"Ocorreu um erro ao verificar os e-mails: {e}")

    finally:
        if 'iamp' in locals() and iamp.state == 'SELECTED':
            iamp.logout()
            print("Logout do e-mail realizado.")

    return tarefas_encontradas

def enviar_notificacao_telegram(nome_tarefa):
    """
    Esta função formata uma mensagem e a envia para seu chat no Telegram
    através do bot que criamos.
    """
    print(f"Preparando para enviar notificação sobre: '{nome_tarefa}'...")
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    mensagem = f"""
        🔔 *Nova Tarefa no Asana!* 🔔

        Uma nova tarefa foi atribuída a você:
        📋: `{nome_tarefa}`

        Verifique o Asana para mais detalhes.
        """

    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': mensagem,
        'parse_mode': 'Markdown'
    }

    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Notificação enviada com sucesso para o Telegram!")
        else:
            print(f"Falha ao enviar notificação. Resposta do Telegram: {response.text}")
    except Exception as e:
        print(f"Ocorreu um erro ao conectar com o Telegram: {e}")
        
if __name__ == "__main__":
    novas_tarefas = verificar_novas_tarefas_asana()

    if novas_tarefas:
        print(f"\nResumo: {len(novas_tarefas)} nova(s) tarefa(s) para notificar.")
        for tarefa in novas_tarefas:
            enviar_notificacao_telegram(tarefa)
    else:
        print("\nResumo: Nenhuma nova tarefa encontrada. Tudo em dia!")

    print("\n--- Automação concluída ---")