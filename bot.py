import logging
import telegram
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import pandas as pd
import requests
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger('telegram_bot')


def start(update, context):
    chat_id = update.effective_chat.id
    user = update.effective_user.first_name
    # Initiate the conversation with the user using the chat id to identify where to direct the response.
    context.bot.send_message(chat_id=chat_id, text=f"Hello there, {user}! Provide the number of a Rossmans's store and I will give you the sales prediction of the next six weeks.")

    
def load_database(update, context):

    user = update.effective_user.first_name
    store_id = str(update.message.text)
    chat_id = update.effective_chat.id

    try:
        store_id = int(store_id.replace('/', ''))
    except ValueError:
        store_id = 'error'
        context.bot.send_message(chat_id=chat_id, text=f'Sorry {user}. You must type a store number id.')

    if store_id != 'error':

        df = pd.read_csv('DATA/test.csv')
        store = pd.read_csv('DATA/store.csv')

        raw_data = pd.merge(df, store, how='left', on='Store')

        df_store = raw_data.query(f'Store=={store_id}')

    if not df_store.empty:

        df_store = df_store.query(f'Open != 0 & ~Open.isnull() & Store=={store_id}').drop('Id', axis=1)
        data = df_store.to_json(orient='records')

    else:

        data = 'error'

    return data

def predict(update, context):

    user = update.effective_user.first_name
    data = load_database(update, context)
    chat_id = update.effective_chat.id
    # Chamada na API
    url = 'https://brenoteixeira-rossmann-api-handler-73wgwz.streamlit.app/'
    header = {'Content-type': 'application/json'}

    if data != 'error':

        r = requests.post(url, headers=header, data=data)
        data = pd.DataFrame(r.json())
        prediction = data.prediction.sum()
        message = f'The store {data.store[0]} will sell ${prediction:,.2f} in the next six weeks.'

        context.bot.send_message(chat_id=chat_id, text=message)

    else:

        context.bot.send_message(chat_id=chat_id, text=f'{user}, this isn\'t a valid store ID.')




if __name__ == '__main__':

    telegram_bot_token = '5857411880:AAE-s0IVAn912M-kh8KgbjuB9FtBeCiNq5A'

    updater = Updater(token=telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher



    ## run the start function when the user invokes the /start command
    dispatcher.add_handler(CommandHandler('start', start))
    #
    #dispatcher.add_handler(MessageHandler(Filters.text, load_database))

    dispatcher.add_handler(MessageHandler(Filters.text, predict))
    ## invoke the get_prediction fucntion whe the user sends a message
    # dispatcher.add_handler(MessageHandler(Filters.text, get_prediction))


    updater.start_webhook(listen='0.0.0.0',
                          port=int(os.environ.get('PORT', 3000)),
                          url_path=telegram_bot_token,
                          webhook_url = 'https://brenoteixeira-rossmann-bot.streamlit.app/' + telegram_bot_token)

