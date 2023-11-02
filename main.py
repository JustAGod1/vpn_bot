import telebot
import csv
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
PASSPHRASE = os.getenv('PASSPHRASE')
bot = telebot.TeleBot(BOT_TOKEN)
prefix = 'docker-compose -f ~/vpn/docker-compose.yml run --rm openvpn'


@bot.message_handler(commands=['start'])
def handle_text(message):
    answer = 'welcum!'
    bot.send_message(message.from_user.id, answer)


@bot.message_handler(func=lambda message: message.from_user.id == 450567117 and message.text.split()[0] == 'new')
def handle_text(message):
    client = message.text.split()[1] if len(message.text.split()) > 1 else None
    if client:
        process = subprocess.Popen([f'{prefix} easyrsa build-client-full {client} nopass'],
                                   stdin=subprocess.PIPE, shell=True, text=True)
        stdin = f'{PASSPHRASE}\n'
        process.communicate(stdin)
        answer = f'{client} probably created'
    else:
        answer = 'Укажите client: <code>new client</code>'
    bot.send_message(message.from_user.id, answer, parse_mode='HTML')


@bot.message_handler(func=lambda message: message.from_user.id == 450567117 and message.text.split()[0] == 'get')
def handle_text(message):
    client = message.text.split()[1] if len(message.text.split()) > 1 else None
    if client:
        with open(f'certificate.ovpn', 'w') as cert:
            process = subprocess.Popen([f'{prefix} ovpn_getclient {client}'], stdout=cert, shell=True)
            process.communicate()
        with open(f'certificate.ovpn', 'r') as cert:
            bot.send_document(message.from_user.id, cert)
        os.remove(f'certificate.ovpn')
    else:
        answer = 'Укажите client: <code>get client</code>'
        bot.send_message(message.from_user.id, answer, parse_mode='HTML')


@bot.message_handler(func=lambda message: message.from_user.id == 450567117 and message.text.split()[0] == 'rm')
def handle_text(message):
    client = message.text.split()[1] if len(message.text.split()) > 1 else None
    if client:
        process = subprocess.Popen([f'{prefix} easyrsa revoke {client}'], stdin=subprocess.PIPE, shell=True, text=True)
        stdin = f'yes\n{PASSPHRASE}\n'
        process.communicate(stdin)
        process = subprocess.Popen([f'{prefix} easyrsa gen-crl'], stdin=subprocess.PIPE, shell=True, text=True)
        stdin = f'{PASSPHRASE}\n'
        process.communicate(stdin)
        process = subprocess.Popen([f'{prefix} ash'], stdin=subprocess.PIPE, shell=True, text=True)
        stdin = f'cp -f "$EASYRSA_PKI/crl.pem" "$OPENVPN/crl.pem"\nchmod 644 "$OPENVPN/crl.pem"\n'
        process.communicate(stdin)
        answer = f'{client} probably deleted'
    else:
        answer = 'Укажите client: <code>rm client</code>'
    bot.send_message(message.from_user.id, answer, parse_mode='HTML')


@bot.message_handler(func=lambda message: message.from_user.id == 450567117 and message.text.split()[0] == 'all')
def handle_text(message):
    process = subprocess.Popen([f'{prefix} ovpn_listclients'], stdout=subprocess.PIPE, shell=True, text=True)
    stdout = process.communicate()[0]
    reader = csv.DictReader(stdout.splitlines())
    answer = ''.join(f'`{row["name"]}`: {row["status"]}\n' for row in reader)
    bot.send_message(message.from_user.id, answer, parse_mode='Markdown')


if __name__ == '__main__':
    print('Get me:\n', bot.get_me(), '\n==========')
    bot.polling(none_stop=True)
