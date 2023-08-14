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


def recommend_candidates(job_id, number_of_candidates):
    # Connect to the candidate and job databases
    connection_to_db = create_db_connection("localhost", "root", "", "myarticles",3306)
    # connection_to_db = create_db_connection("database", "root", "root", "kripton-talent-db",3310)

    # Define SQL queries
    candidates_query = """
        SELECT 
        candidates.id , 
        candidates.name ,
        
     
        GROUP_CONCAT(candidates.skills SEPARATOR ' ') AS skills FROM candidates 
      
        GROUP BY candidates.id;
    """
    job_query = """
        SELECT 
        job_offers.id ,
        job_offers.title , 
        GROUP_CONCAT(job_offers.required_skills SEPARATOR ' ') AS skills
        FROM job_offers
       
        WHERE job_offers.id = {}
    """.format(job_id)

    # Retrieve job details and candidates
    job = read_query(connection_to_db, job_query)[0]
    job_designation, job_skills = job[1], job[2]
    candidates = read_query(connection_to_db, candidates_query)


    candidates_df = pd.DataFrame(candidates,
                                 columns=['id', 'name', 
                                           'skills'])

    # Perform TF-IDF vectorization and cosine similarity calculation
    vectorizer = TfidfVectorizer()
    vectorizer.fit([job_designation, job_skills])
    job_title_vector = vectorizer.transform([job_designation])
    job_skills_vector = vectorizer.transform([job_skills])
    candidate_skill_vector = vectorizer.transform(candidates_df['skills'])
  
    skills_cosine_similarity = cosine_similarity(job_skills_vector, candidate_skill_vector).flatten()
  

    # Add similarity scores to the candidates dataframe and sort by score
    candidates_df["cosine_similarity_score"] = (skills_cosine_similarity) / 2
    candidates_df["matching_score"] = candidates_df["cosine_similarity_score"] * 100
    sorted_candidates = candidates_df.sort_values(by="cosine_similarity_score", ascending=False)

    # Retrieve the top 2 candidates and create a list of candidate dictionaries
    top_resumes_df = sorted_candidates.head(number_of_candidates)
    skills_list = []
    candidates_list = []
    final_candidates_list = []

    for index, row in top_resumes_df.iterrows():
        candidate_id = row['id']
       

        email = row['name']
      
        skills = row['skills']
        skills = skills.replace("[", "").replace("]", "").replace("'", "")
        skills_list.append(skills)

        match_percentage = round(row['matching_score'], 2)
        candidates_list.append(
            f"{candidate_id},{email},{match_percentage}")

    for i in range(len(candidates_list)):
        pro = candidates_list[i].split(",")
        skill = skills_list[i].split(',')
        pro.append(skill)

        pro_key = ['id', 'name', 'score', 'skills']
        pro_dict = dict(zip(pro_key, pro))
        final_candidates_list.append(pro_dict)

    return final_candidates_list
