from flask import Flask ,jsonify,render_template,request

from jobs.routes import app_bp

import os
from  extractpdf import extract_data_from_resume
import nltk
import json
from matcher import condidatur_matcher
from matcher import job_matcher
#from condidatmatcher import matchers,preprocess_text

#from matcher  import Matchercondidat


from functools import reduce

import mysql.connector


mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="myarticles"
)
#Function to remove white space
def remove(string):
    string  = str(string)
    return reduce(lambda x, y: (x+y) if (y != " ") else x, string, "")

app = Flask(__name__)


app.register_blueprint(app_bp)

app.config['SECRET_KEY'] = 'azerty147852369az'







UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def insertmatcher(username , score ):
    cur = mysql_conn.cursor()
    cur.execute("INSERT INTO matches (candidate_name, match_score) VALUES (%s, %s)", (username, score))
    mysql_conn.commit()
    cur.close()
    return "ok"

@app.route('/')
def index():
    return render_template('upload.html')


@app.route("/api/v1")
def home():
    return jsonify({
        "data": "hello there "
    })



@app.route('/add_candidate', methods=['POST'])
def add_candidate():
    data = request.json
    name = data['name']
    skills = data['skills']

    cur = mysql_conn.cursor()
    cur.execute("INSERT INTO candidates (name, skills) VALUES (%s, %s)", (name, skills))
    mysql_conn.commit()
    cur.close()

    return jsonify({'message': 'Candidate added successfully'})

@app.route('/add_job_offer', methods=['POST'])
def add_job_offer():
    data = request.json
    title = data['title']
    required_skills = data['required_skills']

    cur = mysql_conn.cursor()
    cur.execute("INSERT INTO job_offers (title, required_skills) VALUES (%s, %s)", (title, required_skills))
    mysql_conn.commit()
    cur.close()

    return jsonify({'message': 'Job offer added successfully'})

@app.route('/match_jobs', methods=['POST'])
def match_jobs():
    candidate_skills = request.json['skills']

    cur = mysql.cursor()
    cur.execute("SELECT id, title, required_skills FROM job_offers")
    job_offers = cur.fetchall()
    cur.close()

    matched_jobs = []
    for job_offer in job_offers:
        required_skills = job_offer['required_skills'].split(',')
        if all(skill.strip() in candidate_skills for skill in required_skills):
            matched_jobs.append({'id': job_offer['id'], 'title': job_offer['title']})

    return jsonify({'matched_jobs': matched_jobs})



@app.route('/match_jobs/<job_id>/<job_title>/<job_data>', methods=['GET'])
def matchs_jobs(job_id,job_title,job_data):
    

    
   

    
    job_query = """
        SELECT 
        job_offers.id ,
        job_offers.title , 
        GROUP_CONCAT(job_offers.required_skills SEPARATOR ' ') AS skills
        FROM job_offers
       
        WHERE job_offers.id = {}
    """.format(job_id)

    job = condidatur_matcher.read_query(mysql_conn, job_query)[0]
    _, job_skills = job[1], job[2]
   
    print (job_skills)
    #cursor = mysql_conn.cursor()
 
    #cursor.execute("SELECT name, skills FROM candidates")
    candidates_query = """
        SELECT 
        candidates.id , 
        candidates.name ,
        candidates.skills
        
     
        GROUP_CONCAT(candidates.skills SEPARATOR ' ') AS skills FROM candidates 
      
        GROUP BY candidates.id;
    """
    query = "SELECT name, LOWER(skills) FROM candidates"
    candidates =condidatur_matcher.read_query(mysql_conn,query)

    matched_candidates = []

    for candidate in candidates:
        candidate_name, candidate_skills = candidate
        candidate_skill_tokens = nltk.word_tokenize(candidate_skills)
        job_skill_tokens = nltk.word_tokenize(job_skills)
        print (candidate_skill_tokens)


        # Calculate similarity between job skills and candidate skills
        common_skills = set(candidate_skill_tokens) & set(job_skill_tokens)
        similarity_score = len(common_skills) / len(job_skill_tokens)

        print (similarity_score)

        if similarity_score >= 0.5:  # You can adjust the threshold as needed
            matched_candidates.append(candidate_name)
            insertmatcher(candidate_name,similarity_score)


    return jsonify({'matched_candidates': matched_candidates})

@app.route('/upload', methods=['POST'])
def upload():
    nltk.download('averaged_perceptron_tagger')
    if 'resume' not in request.files:
        return "No file part"

    resume_file = request.files['resume']
    if resume_file.filename == '':
        return "No selected file"
    
    resumefilename=remove(resume_file.filename)
    
    # Save the uploaded file
    resume_path = os.path.join('uploads',resumefilename )
    resume_file.save(resume_path)

    # Call the function to extract data from the uploaded resume
    extracted_data = extract_data_from_resume(resume_path)
    print (extracted_data["skills"])
    
    

    skills =  extracted_data['skills'].split(',')
    username = extracted_data['mail']

    dataf = {}

    skil = ' '.join(skills)
    cv_path  =f'/show/PDFs/{resumefilename}'

    cur = mysql_conn.cursor()
    cur.execute("INSERT INTO candidates (name, skills,cv) VALUES (%s, %s,%s)", (username, skil,cv_path))
    mysql_conn.commit()
    cur.close()

    



    
    # matcher_ = Matchercondidat(  ["java"],skills=extracted_data["skills"].split(','))
    # cv_file=  resumefilename.split(".")[0]
    # print(cv_file)

    # matcher_.chckmatch(extracted_data,f"http://localhost:5000/show/PDFs/{cv_file}")




   
    

 
    
    
    return jsonify( {'data':extracted_data,'skills':skills}  )


import  os 
from flask import send_from_directory

@app.route('/show/PDFs/<filename>')
def send_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], f'{filename}.pdf')


@app.route("/files")
def   myfiles():


    ls_ =  os.listdir(os.getcwd() + "/uploads")

    return jsonify({'cv':ls_})




@app.route('/api/recommend/<int:job_id>/<int:number_of_candidates>', methods=['GET'])
def recommend_candidates_for_job(job_id, number_of_candidates):
    return jsonify(condidatur_matcher. recommend_candidates(job_id, number_of_candidates))


@app.route('/api/recommend_job/<int:candidate_id>/<int:number_of_jobs>', methods=['GET'])
def recommend_jobs_for_candidates(candidate_id, number_of_jobs):
    return jsonify(job_matcher.recommend_jobs(candidate_id, number_of_jobs))

if __name__ =='__main__':
    app.run(debug=True, host='localhost',port=5002)
