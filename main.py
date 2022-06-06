from src.ui import start_main_app

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    start_main_app()  # то запускаем функцию main()
    exit()  # TODO: I think this is not good, but sometimes Django breaks here
