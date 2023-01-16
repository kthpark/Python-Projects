import requests
import sys
from bs4 import BeautifulSoup

url = 'https://context.reverso.net/translation/'
headers = {'User-Agent': 'Mozilla/5.0'}

languages = ['arabic', 'german', 'english', 'spanish', 'french', 'hebrew', 'japanese',
             'dutch', 'polish', 'portuguese', 'romanian', 'russian', 'turkish']


def output(y, translations, examples, output_num):
    print(f'{y.title()} Translations:')
    print(*translations[:output_num], sep='\n')

    print(f'\n{y.title()} Examples:')
    print(*examples[:output_num * 3], sep='\n')


def export_to_file(word, y, translations, examples, output_num):
    file_name = f'{word}.txt'
    with open(file_name, 'a', encoding='utf-8') as file:
        print(f'{y.title()} Translations:', file=file)
        print(*translations[:output_num], file=file, sep='\n')

        print(f'\n{y.title()} Examples:', file=file)
        print(*examples[:output_num * 3], file=file, sep='\n')


def parser(trans_page):
    r = requests.get(trans_page, headers=headers)
    soup = BeautifulSoup(r.content, 'html.parser')

    trans_tags = soup.find_all('span', {'class': 'display-term'})
    examples_tags = soup.find('section', id="examples-content").find_all('span', class_="text")

    if trans_tags and examples_tags:
        translations, examples = [t.text for t in trans_tags], [e.text.strip() for e in examples_tags]
        i = 2
        while i < len(examples):
            examples.insert(i, ' ')
            i += 3
        return translations, examples


def translation(x, y, word):
    language_1 = x
    languages_2 = []
    if y != 'all':
        languages_2.append(y)
    else:
        for lang in languages:
            if lang != x:
                languages_2.append(lang)
    for language_2 in languages_2:
        trans_page = f'{url}{language_1}-{language_2}/{word}'
        if parser(trans_page):
            translations, examples = parser(trans_page)

            output_num = 1

            output(language_2, translations, examples, output_num)
            export_to_file(word, language_2, translations, examples, output_num)
        else:
            print(f'Sorry, unable to find {word}')
            break


def check_input(x, y):
    if x not in languages:
        print(f"Sorry, the program doesn't support {x}")
        return False
    elif y not in languages and y != 'all':
        print(f"Sorry, the program doesn't support {y}.")
        return False
    return True


def main():
    x, y, word = sys.argv[1].lower(), sys.argv[2].lower(), sys.argv[3]

    if check_input(x, y):
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            translation(x, y, word)
        else:
            print('Something wrong with your internet connection')


if __name__ == "__main__":
    main()
    