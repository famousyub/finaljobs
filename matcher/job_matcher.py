import mysql.connector
import pandas as pd
from mysql.connector import Error
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def create_db_connection(host_name, user_name, user_password, db_name,port):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name,
            port=port
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection


def read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as err:
        print(f"Error: '{err}'")


def recommend_jobs(candidate_id,number_of_jobs):
    # Connect to the candidate and job databases
    connection_to_db = create_db_connection("localhost", "root", "", "kripton-talent-db",3306)
    # connection_to_db = create_db_connection("database", "root", "root", "kripton-talent-db",3310)
    
    # Define SQL queries
    candidates_query = """
        SELECT 
        candidates.id , 
        candidates.designation, 
        GROUP_CONCAT(candidate_skills.skill SEPARATOR ', ') AS skills FROM candidates 
        INNER JOIN candidate_skills ON candidates.id = candidate_skills.candidate_id 
        WHERE candidates.id = {}
    """.format(candidate_id)
    job_query = """
        SELECT 
        jobs.id ,
        jobs.title ,
        jobs.company,
        jobs.status,
        jobs.employment_type,
        GROUP_CONCAT(job_required_skills.skill SEPARATOR ', ') AS skills
        FROM jobs
        INNER JOIN job_required_skills ON jobs.id = job_required_skills.job_id
        GROUP BY jobs.id;
    """

    # Retrieve job details and candidates

    candidate = read_query(connection_to_db,candidates_query)[0]
    candidate_designation,candidate_skills = candidate[1],candidate[2]
    jobs = read_query(connection_to_db,job_query)
    jobs_df = pd.DataFrame(jobs,columns=['id','title','company','status','employment_type','skills'])


    # Perform TF-IDF vectorization and cosine similarity calculation
    vectorizer = TfidfVectorizer()
    vectorizer.fit([candidate_designation, candidate_skills])
    candidate_title_vector = vectorizer.transform([candidate_designation])
    candidate_skills_vector = vectorizer.transform([candidate_skills])
    job_skill_vector = vectorizer.transform(jobs_df['skills'])
    job_title_vector = vectorizer.transform(jobs_df['title'])
    skills_cosine_similarity = cosine_similarity(candidate_skills_vector, job_skill_vector).flatten()
    designation_cosine_similarities = cosine_similarity(candidate_title_vector, job_title_vector).flatten()

    # Add similarity scores to the candidates dataframe and sort by score
    jobs_df["cosine_similarity_score"] = (skills_cosine_similarity + designation_cosine_similarities) / 2
    jobs_df["matching_score"] = jobs_df["cosine_similarity_score"] * 100
    sorted_candidates = jobs_df.sort_values(by="cosine_similarity_score", ascending=False)

    top_resumes_df = sorted_candidates.head(number_of_jobs)
    skills_list = []
    jobs_list = []
    final_jobs_list = []

    for index, row in top_resumes_df.iterrows():
        job_id = row['id']
        title = row['title']
        company = row['company']
        status = row['status']
        employment_type = row['employment_type']
        skills = row['skills']
        skills = skills.replace("[", "").replace("]", "").replace("'", "")
        skills_list.append(skills)

        match_percentage = round(row['matching_score'], 2)
        jobs_list.append(f"{job_id},{title},{company},{status},{employment_type},{match_percentage}")

    for i in range(len(jobs_list)):
        pro = jobs_list[i].split(",")
        skill = skills_list[i].split(',')
        pro.append(skill)

        pro_key = ['id', 'title','company','status', 'employment_type', 'score', 'skills']
        pro_dict = dict(zip(pro_key, pro))
        final_jobs_list.append(pro_dict)

    return final_jobs_list



