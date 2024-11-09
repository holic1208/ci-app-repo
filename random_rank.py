from flask import Flask, render_template, request, redirect, url_for, session
import random
import datetime
import json
import boto3
import pytz
import logging

app = Flask(__name__)
app.secret_key = 'dev'  # Adding a secret key for a session ex.dev,stg ...

S3_BUCKET_NAME = "for-cicd-test-tournament-s3" # please edit this part
s3_client = boto3.client('s3')

def load_youtube_links(file_path="youtube_links.txt"):
    with open(file_path, "r") as file:
        links = [line.strip() for line in file.readlines() if line.strip() and not line.startswith("#")]
    return links

def generate_pairs(links):
    pairs = [(links[i], links[i + 1]) for i in range(0, len(links), 2)]
    return list(pairs)

def save_winner_to_s3(winner_link, s3_client=None):
    print("[DEBUG] save_winner_to_s3 함수 시작")
    try:
        if s3_client is None:
            s3_client = boto3.client('s3')

        korea_time = datetime.datetime.now(pytz.timezone("Asia/Seoul"))
        timestamp = korea_time.strftime("%Y-%m-%dT%H:%M:%S")

        winner_data = {
            "winner": winner_link,
            "timestamp": timestamp
        }

        file_name = f"winner_{timestamp}.json"
        
        print(f"[DEBUG] Uploading to S3: Bucket={S3_BUCKET_NAME}, Key=tournament_logs/{file_name}")
        print(f"[DEBUG] Data being uploaded: {winner_data}")
        
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=f"tournament_logs/{file_name}",
            Body=json.dumps(winner_data),
            ContentType="application/json"
        )
        print(f"[SUCCESS] Successfully uploaded to S3: {file_name}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to upload to S3: {str(e)}")
        import traceback
        print(traceback.format_exc())  # Output detailed error information
        return False

@app.route('/')
def index():
    youtube_links = load_youtube_links()
    random.shuffle(youtube_links)

    pairs = generate_pairs(youtube_links)

    # Save tournament status to session
    session['current_pairs'] = pairs
    session['selected_links'] = []
    session['round_stage'] = "16강"
    session['current_round'] = 1

    return render_template('tournament.html',
                         pair=pairs[0],
                         round_stage="16강",
                         round_number=1)

@app.route('/choose', methods=['POST'])
def choose():
    print("\n===== CHOOSE ROUTE START =====")
    print("[DEBUG] Current stage:", session.get('round_stage'))
    print("[DEBUG] Current pairs length:", len(session.get('current_pairs', [])))
    print("[DEBUG] Selected links:", session.get('selected_links'))
    
    if 'current_pairs' not in session:
        print("[DEBUG] No current_pairs in session, redirecting to index")
        return redirect(url_for('index'))
        
    current_pairs = session.get('current_pairs', [])
    selected_links = session.get('selected_links', [])
    round_stage = session.get('round_stage', "16강")
    current_round = session.get('current_round', 1)
    
    chosen_link = request.form.get('choice')
    print(f"[DEBUG] Chosen link: {chosen_link}")
    
    if not chosen_link:
        print("[DEBUG] No chosen link, redirecting to index")
        return redirect(url_for('index'))
        
    selected_links.append(chosen_link)
    session['selected_links'] = selected_links
    print(f"[DEBUG] Updated selected_links: {selected_links}")
    
    # If all matches in the current round are not finished
    if len(selected_links) < len(current_pairs):
        print(f"[DEBUG] Moving to next match in current round: {len(selected_links) + 1}")
        next_pair = current_pairs[len(selected_links)]
        session['current_round'] = len(selected_links) + 1
        return render_template('tournament.html',
                             pair=next_pair,
                             round_stage=round_stage,
                             round_number=len(selected_links) + 1)
    
    # If all matches of the current round are over
    if len(selected_links) == len(current_pairs):
        print(f"[DEBUG] Current round finished. Round stage: {round_stage}")
        
        # When the final round is over
        if len(current_pairs) == 1:
            print("\n===== FINAL ROUND FINISHED =====")
            print(f"[DEBUG] Winner: {selected_links[0]}")
            try:
                print("[DEBUG] Attempting to save to S3...")
                upload_success = save_winner_to_s3(selected_links[0])
                print(f"[DEBUG] S3 upload result: {upload_success}")
            except Exception as e:
                print(f"[ERROR] S3 upload failed: {str(e)}")
                import traceback
                print(traceback.format_exc())
            return render_template('winner.html', winner=selected_links[0])
            
        # Get ready for the next round
        print("[DEBUG] Preparing next round...")
        new_pairs = generate_pairs(selected_links)
        session['current_pairs'] = new_pairs
        session['selected_links'] = []
        session['current_round'] = 1
        
        if round_stage == "16강":
            session['round_stage'] = "8강"
        elif round_stage == "8강":
            session['round_stage'] = "4강"
        elif round_stage == "4강":
            session['round_stage'] = "결승"
            
        print(f"[DEBUG] Moving to next round: {session['round_stage']}")
        return render_template('tournament.html', 
                             pair=new_pairs[0], 
                             round_stage=session['round_stage'], 
                             round_number=1 if session['round_stage'] != "결승" else None)
                             
    print("[DEBUG] Unexpected state, redirecting to index")
    return redirect(url_for('index'))
