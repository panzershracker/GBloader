import requests, os, re, wget
from bs4 import BeautifulSoup as soup


class Downloader():

    def __init__(self, les_url, login, password):
        self.les_url = les_url
        self.login = login
        self.password = password

    def auth(self, login, password):
        # Авторизует пользователя.
        # Принимает login, password.

        session.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0'
        resp = session.get('https://geekbrains.ru/login')
        auth_token = soup(resp.text, 'lxml').select_one('input[name="authenticity_token"]')['value']
        resp = session.post(
            'https://geekbrains.ru/wanna_captcha',
            data={
                'user[email]': login,
                'user[password]': password,
                'user[remember_me]': 0,
                'authenticity_token': auth_token,
                'utf8': '✓'
            }
        )
        user_name = soup(resp.text, 'lxml').select_one('li.controls > a.avatar > img, alt')['alt']
        print('Вы вошли в систему как', user_name)

    def define_folder_name(self, les_url):
        # Определяет название папки с уроками
        # Принимает ссылку урока
        # Возвращает название папки


        ses = session.get(les_url)
        folder = soup(ses.text, 'lxml').select_one('h2 > span.course-title').text
        return folder

    def regex_filter(self, file_or_folder_name):
        # Проверяет название папки или файла на недопустимые символы при именовании.
        # Принимает имя файла или папки
        # Возвращает новое имя, или старое, если оно соответствует условию

        regex = '[?]|[\\]|[/]|[\|]|[<]|[>]|[\"]|[:]|[*]'
        name_check = re.findall(regex, file_or_folder_name)
        if len(name_check) == 0:
            return file_or_folder_name
        else:
            new_name = ''
            for i in name_check:
                new_name = file_or_folder_name.replace(i, '.')
                return new_name

    def folder_exists(self, les_url, regex_folder_name):
        # Проверка на наличие папки с уроком
        # Принимает ссылку урока, название папки
        # Создает папку, если ее не существует

        folder = regex_folder_name
        print(f'Проверка на наличие папки "{folder}"...')
        if os.path.exists(folder) is True:
            print(f'Папка "{folder}" существует.')
            pass
        else:
            os.makedirs(folder)
            print(f'Папка "{folder}" создана.')

    def les_amount(self, les_url):
        # Проверяет кол-во уроков в курсе
        # Принимает ссылку урока
        # Возвращает кол-во уроков всего

        ses = session.get(les_url)
        les_headers_list = soup(ses.text, 'lxml').select('span.lesson-header__number')
        les_list = []
        for i in les_headers_list:
            if i.text.startswith('Урок'):
                les_list.append(i.text)
        les_amount = len(les_list)
        print(f'Всего уроков в курсе: {les_amount}')
        return les_amount

    def available_les_count(self, les_url):
        # Показывает кол-во доступных для скачивания уроков
        # Принимает ссылку на урок
        # Возвращает кол-во доступных для скачивания уроков

        ses = session.get(les_url)
        checks = soup(ses.text, 'lxml').select('span.lesson-header__status-icon > svg.svg-icon.icon-check')
        available_les_count = len(checks) - 1
        print(f'Доступно для скачивания: {available_les_count}')
        return available_les_count

    def next_les_link_generate(self, les_url, i):
        # Создает ссылку на следующий видео-урок
        # Принимает ссылку на урок, значение итератора
        # Возвращает ссылку на следующий урок

        http, slash, site, category, les_number = les_url.split('/')
        next_les_number = int(les_number) + i
        next_les_link = (http + '//' + site + '/' + category + '/' + str(next_les_number))

        return next_les_link

    def file_link(self, next_les_link):
        # Извлекает ссылку на видео материал
        # Получает ссылку на урок
        # Возвращает ссылку на видео

        ses = session.get(next_les_link)
        video_link = soup(ses.text, 'lxml').select_one('li.lesson-contents__list-item > a')['href']
        return video_link

    def concat_name(self, next_les_link):
        # Создает имя файла ( Номер урока + тема урока + расширение)
        # Получает ссылку на урок
        # Возвращает готовое имя файла

        ses = session.get(next_les_link)

        name = soup(ses.text, 'lxml').select_one('gb__learning > div > header > div > h3').text
        file_name = name + '.mp4'
        return file_name

    def exists_check(self, regex_file, regex_folder_name):
        # Проверяет файл на наличие в папке перед закачкой
        # Принимает готовое имя файла, название папки
        # Возвращает: если файл НЕ в папке - False, если в папке - True

        dir = os.listdir(regex_folder_name)
        file_name = regex_file
        if file_name in dir:
            return True
        else:
            return False

    def exists_check_web(self, file_link, next_les_link, regex_folder_name, global_iter):
        # Проверяет наличие файла по селектору. Если файл не на месте - скачивает весь видео материал данного урока
        # Принимает ссылку на файл, ссылку на след. урок, корректное имя папки, значение итератора.
        # Возвращает: если селектор верен - True, если нет - скачивает все видео урока, и возвращает
        # альтернативное имя файла

        ses = session.get(next_les_link)
        all_video_links = soup(ses.text, 'lxml').select('#right-side-wrapper > div.lesson-contents > ul > li > a')
        les_num = soup(ses.text, 'lxml').select_one('span.lesson-header__number').text
        if file_link.endswith('.mp4'):
            return True
        else:
            for i in all_video_links:
                if i['href'].endswith('.mp4'):
                    print(f'css селектор не верный. Загрузка всех видео {global_iter} урока. Ожидайте...')
                    wget.download(i['href'], regex_folder_name + '/' + les_num + '.' + i.text)
                    alt_file_name = les_num + '.' + i.text
                    return alt_file_name
                else:
                    pass

    def _docs_download(self, next_les_link, define_folder_name):
        # TODO метод скачивания методичек и презентаций.

        ses = session.get(next_les_link)
        doc_link = soup(ses.text, 'lxml').select('#right-side-wrapper > div.lesson-contents > ul > li > a')
        for i in doc_link:
            if i['href'].endswith('.mp4'):
                pass
            else:
                wget.download(i['href'], define_folder_name + '/' + i.text + '.html')

    def contents_table_add(self, regex_folder_name, file_name):
        # Добавляет в тект. файл список уроков и темы уроков
        # Принимает название папки, имя файла
        # Добавляет запись в текст. файл

        with open(regex_folder_name + '/' + 'Оглавление' + regex_folder_name + '.txt', 'a') as file:
            file.write(f'\n {file_name}\n')

    def file_download(self, regex_folder_name, regex_file, video_link, exists_check, exists_web_check):
        # Скачивает целевой файл в папку. Для использования - импортировать wget, нет статус бара.
        # Принимает имя папки, имя файла, ссылку на видео, проверку на наличие, проверку на наличие на сервере
        # Результат - скачанный файл или сообщение о его наличии

        if exists_check == False:
            if exists_web_check == True:
                print(f'Скачиваем "{regex_file}"...')
                wget.download(video_link, regex_folder_name + '/' + regex_file)
            else:
                pass
        elif exists_check == True:
            print(f'Файл "{regex_file}" уже существует.')
        else:
            pass

    def check_file_size(self, file_link, regex_folder_name, regex_file, exists_check_web):
        # Сравнивает размер файла на сервере и в локальном хранилище
        # Принимает сслыку на файл, имя папки, имя файла, наличие на сервере
        # Возвращает: если размеры совпадают - True, если нет - информирует о несоответствии.

        if exists_check_web != True:
            filesize = os.path.getsize(regex_folder_name + '/' + exists_check_web)
        else:
            filesize = os.path.getsize(regex_folder_name + '/' + regex_file)
            testread = requests.head(file_link)
            websize = int(testread.headers['Content-length'])
            if filesize == websize:
                print('Готово!')
                return True
            else:
                print(f'!Размер загруженного файла "{regex_file}" не совпадает с размером на сервере.')
                print(f'Попробуйте самостоятельно скачать видео с сайта')
                return False

    def _progress_bar_download(self, define_folder_name, concat_name, video_link, exists_check):
        # Прогресс бар работает некорректно. Переделать программу под граффическую оболочку.

        testread = requests.head(video_link)
        websize = int(testread.headers['Content-length'])
        r = requests.get(video_link, stream=True)  # actual download full file
        if exists_check == False:
            print(f'Скачиваем "{concat_name}"...')
            with open(define_folder_name + '/' + concat_name, 'wb') as f:
                pbar = tqdm(total=int(websize / 1024))
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        pbar.update()
                        f.write(chunk)
            print(' - Готово!')
            return True
        else:
            print(f'Файл "{concat_name}" уже существует.')
            return True


def webinar_format(les_url, login, password):
    downloader = Downloader(les_url, login, password)
    downloader.auth(login, password)
    folder_name = downloader.define_folder_name(les_url)
    regex_folder_name = downloader.regex_filter(folder_name)
    folder_exists = downloader.folder_exists(les_url, regex_folder_name)
    les_amount = downloader.les_amount(les_url)
    available_les_count = downloader.available_les_count(les_url)
    i = 0
    while i != available_les_count:
        next_les_link = downloader.next_les_link_generate(les_url, i)
        file_link = downloader.file_link(next_les_link)
        file_name = downloader.concat_name(next_les_link)
        regex_file = downloader.regex_filter(file_name)
        file_exists = downloader.exists_check(regex_file , regex_folder_name)
        web_exists = downloader.exists_check_web(file_link, next_les_link, regex_folder_name, i)
        content = downloader.contents_table_add(regex_folder_name, regex_file_name)
        download = downloader.file_download(regex_folder_name, regex_file , file_link, file_exists, web_exists)
        size_check = downloader.check_file_size(file_link, regex_folder_name, regex_file, web_exists)
        i += 1
        continue


def video_format(les_url, login, password):
    # Не проверяет кол-во доступных уроков

    downloader = Downloader(les_url, login, password)
    downloader.auth(login, password)
    folder_name = downloader.define_folder_name(les_url)
    regex_folder_name = downloader.regex_filter(folder_name)
    folder_exists = downloader.folder_exists(les_url, regex_folder_name)
    les_amount = downloader.les_amount(les_url)
    i = 0
    while i != les_amount:
        next_les_link = downloader.next_les_link_generate(les_url, i)
        file_link = downloader.file_link(next_les_link)
        file_name = downloader.concat_name(next_les_link)
        regex_file_name = downloader.regex_filter(file_name)
        file_exists = downloader.exists_check(regex_file_name, regex_folder_name)
        web_exists = downloader.exists_check_web(file_link, next_les_link, regex_folder_name, i)
        content = downloader.contents_table_add(regex_folder_name, regex_file_name)
        download = downloader.file_download(regex_folder_name, regex_file_name, file_link, file_exists, web_exists)
        size_check = downloader.check_file_size(file_link, regex_folder_name, regex_file_name, web_exists)
        i += 1
        continue


def start(les_url, les_type, login, password):
    if les_type == 1:
        video_format(les_url, login, password)
    elif les_type == 2:
        webinar_format(les_url, login, password)
    else:
        print('Выберите вариант из списка доступных (1/2)')


with requests.Session() as session:

    les_url = input(str('Введите ссылку к первому уроку:\n'))
    login = input('Введите логин\n')
    password = input('Введите пароль\n')

    les_type = int(input('Выберите тип урока:\n'
                         '1 - Видео формат\n'
                         '2 - Вебинарный формат\n'))

    start(les_url, les_type, login, password)
