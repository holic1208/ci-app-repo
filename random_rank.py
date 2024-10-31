from flask import Flask, render_template, request, redirect, url_for
import random
import datetime
import json
import boto3
import pytz

app = Flask(__name__)

S3_BUCKET_NAME = "for-cicd-test-tournament-s3" # please edit this part
s3_client = boto3.client('s3')

# functions to import YouTube links from external files
def load_youtube_links(file_path="youtube_links.txt"):
    with open(file_path, "r") as file:
        links = [line.strip() for line in file.readlines() if line.strip() and not line.startswith("#")]
    return links

youtube_links = load_youtube_links()
current_pairs = []  # pair of the current round
selected_links = []  # links selected in each round
round_stage = "16강"  # initial Round Status

# pair generation function
def generate_pairs(links):
    # create a pair list by pairing two links
    random.shuffle(links)  # mixing at random
    return [(links[i], links[i + 1]) for i in range(0, len(links), 2)]

# winner record function in S3
def save_winner_to_s3(winner_link, s3_client=None):
    if s3_client is None:
        s3_client = boto3.client('s3')

    korea_time = datetime.datetime.now(pytz.timezone("Asia/Seoul"))
    timestamp = korea_time.strftime("%Y-%m-%dT%H:%M:%S")
    winner_data = {
        "winner": winner_link,
        "timestamp": timestamp
    }
    file_name = f"winner_{timestamp}.json"
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=f"tournament_logs/{file_name}",
        Body=json.dumps(winner_data),
        ContentType="application/json"
    )
    print(f"S3에 우승자 로그를 업로드했습니다: {file_name}")

# 1 round
@app.route('/')
def index():
    global current_pairs, selected_links, round_stage
    selected_links = []
    round_stage = "16강"  # initial Status Settings
    current_pairs = generate_pairs(youtube_links)  # create a round of 16 pair
    return render_template('tournament.html', pair=current_pairs[0], round_stage=round_stage, round_number=1)

# move on to the next round
@app.route('/choose', methods=['POST'])
def choose():
    global current_pairs, selected_links, round_stage
    chosen_link = request.form.get('choice')
    selected_links.append(chosen_link)

    # move to the next pair within the current round
    if len(selected_links) < len(current_pairs):
        next_pair = current_pairs[len(selected_links)]
        return render_template('tournament.html', pair=next_pair, round_stage=round_stage, round_number=len(selected_links) + 1)

    # switch to the next round after the end of the current round
    if len(selected_links) == len(current_pairs):
        if len(selected_links) == 1:
            save_winner_to_s3(selected_links[0])
            return render_template('winner.html', winner=selected_links[0])

        # pair regeneration and round status update
        current_pairs = generate_pairs(selected_links)
        selected_links = []

        # Set the order of round proceedings: 16강 -> 8강 -> 4강 -> 결승
        if round_stage == "16강":
            round_stage = "8강"
        elif round_stage == "8강":
            round_stage = "4강"
        elif round_stage == "4강":
            round_stage = "결승"

        return render_template('tournament.html', pair=current_pairs[0], round_stage=round_stage, round_number=1 if round_stage != "결승" else None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
