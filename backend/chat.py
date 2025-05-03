import google.generativeai as genai
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")

index_name = "brain-tumor-2"

model = SentenceTransformer("bert-base-uncased")
genai.configure(api_key=api_key)
pc = Pinecone(api_key=pinecone_key, environment="us-east-1")
index = pc.Index(index_name)

def embed_text(text):
    return model.encode([text])[0]

def query_pinecone(text):
    vector = embed_text(text)
    response = index.query(vector=vector.tolist(), top_k=3, include_metadata=True)
    return [item["metadata"]["text"] for item in response["matches"]]

def generate_gemini_response(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model.generate_content(prompt).text
    except Exception as e:
        return str(e)
    
def generate_response_with_context(tumor_info, relevant_chunks, user_query):
    detailed_prompt = (
        f"You are a helpful, empathetic,something like doctor,and knowledgeable medical assistant. "
        f"Based on the analysis, the image shows {tumor_info}. "
        f"Additionally, here are some relevant insights related to the query: {relevant_chunks}. "
        f"Provide any general guidance or suggestions the user might need but avoid using disclaimers. "
        f"Focus on being supportive and resourceful. "
        f"Answer the following user query in a general and helpful manner with practical, empathetic, and actionable advice: {user_query}. "
        f"If the query is about medications for brain tumors or related symptoms like headaches, include general medication options like common pain relievers or drugs used for such conditions. "
        f"Otherwise, respond empathetically with relevant advice tailored to the query."
    )
    
    return generate_gemini_response(detailed_prompt)

def handle_chat_query(query, tumor_info, tumor_count):
    chunks = query_pinecone(query)
    tumor_summary = f"Detected {len(tumor_info)} tumors: " + ", ".join([
        f"Tumor {i+1}: {t['confidence']:.2f} at {t['box']}"
        for i, t in enumerate(tumor_info)
    ])
    return generate_response_with_context(tumor_info, chunks, query)
