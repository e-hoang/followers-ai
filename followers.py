from openai import OpenAI
from flask import Flask, render_template, request
import os
import json
import zipfile

api_key = os.getenv('TEST_API_KEY')
if not api_key:
    raise ValueError("TEST_API_KEY is not set. Run `export TEST_API_KEY=sk-...` first.")

client = OpenAI(api_key=api_key)
chat_log = [
]

app = Flask(__name__)
@app.route("/", methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        user_input = request.form['input']
        chat_log.append({'role': 'user', 'content': user_input})
        completion = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=chat_log
        )
        response = completion.choices[0].message.content.strip()
        chat_log.append({'role': 'assistant', 'content': response})
        result = response
        
    return render_template('index.html', result=result, chat_log=chat_log)

@app.route("/upload", methods=['POST'])
def instagram_upload():
    error_message = 'Invalid'
    file = request.files['file']
    if file and file.filename.endswith('.zip'):
        temp = os.path.join('/tmp', file.filename)
        file.save(temp)
        follower_data = analyze_followers(temp)
        return render_template('index.html', result=follower_data,chat_log=chat_log)
    else:
        return error_message

def analyze_followers(zip_filename):
    json_data = {}
    not_following = []
    not_following_back = set()

    with zipfile.ZipFile(zip_filename, 'r') as file:
        for file_name in file.namelist():
            if file_name.endswith('followers_1.json') or file_name.endswith('following.json'):
                with file.open(file_name) as json_file:
                    json_data[file_name] = json.load(json_file)
    
    for data in json_data:
        if data.endswith('followers_1.json'):
            followers = json_data[data]           
            break

    for data in json_data:
        if data.endswith('following.json'):
            following = json_data[data]
            break      

    for entry in followers:
        for profile in entry.get('string_list_data', []):
            user_name = profile.get('value')
            not_following_back.add(profile.get('value'))

    if 'relationships_following' in following:
            for entry in following['relationships_following']:
                for profile in entry.get('string_list_data', []):
                    user_name = profile.get('value')
                    if user_name not in not_following_back:
                        not_following.append(user_name)

    return not_following

if __name__ == '__main__':
    app.run(debug=True)

# app.run(host='0.0.0.0', port=80)
