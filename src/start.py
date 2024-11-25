from multiprocessing import Process
import os

from dotenv import load_dotenv
load_dotenv()

from user_bot import UserBot
from admin_bot import AdminBot

def main():
    userProcess = Process(
        target=UserBot(os.environ.get('TOKEN')).start
    )
    adminProcess = Process(
        target=AdminBot(os.environ.get('ADMIN_TOKEN')).start
    )
    userProcess.start()
    adminProcess.start()
    userProcess.join()
    adminProcess.join()

main()