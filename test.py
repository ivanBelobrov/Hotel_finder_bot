import re

with open('log.log', 'r') as log:
    for i_line in log:
        text = ''
        if 'Received' in i_line:
            date = "".join(re.findall(r'^\S{10}', i_line))
            time = ''.join(re.findall(r'^\S{10}T(\S{8})', i_line))
            command = ''.join(re.findall(r'Received\s(\D+)\scommand', i_line))
            text = text + f'\nКоманда: {command}\nДата запроса: {date}\nВремя запроса: {time}'
        if 'hotels:' in i_line and command in i_line:
            hotels = ''.join(re.findall(r'hotels:\s(.+?)(?:\n|$)', i_line))
            text = text.join(f'\nНайденные отели: {hotels}')
            print(text)
        elif text != '':
            print(text)
