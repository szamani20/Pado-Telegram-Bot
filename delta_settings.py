try:
    f = open('tg_token', 'r')
    TOKEN = f.read().strip()
    f.close()
except Exception as e:
    print(e)
    TOKEN = None

# UPLOAD_FOLDER = '/home/szamani/deltabot/bot/deltabot/static/'
UPLOAD_FOLDER = '/home/szamani/Documents/deltabot/static/'
