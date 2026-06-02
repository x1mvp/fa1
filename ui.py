import streamlit as st
import sys
import os
import requests
import redis
import chromadb
from dotenv import load_dotenv

# Add src to path
sys.path.append('/app/src')
sys.path.append('src')  # For local development

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Open Agent Factory",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Open Agent Factory")
st.markdown("*Local, Open-Source Multi-Agent System*")

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")
    
    # Model selection
    model_options = ["llama3.1:8b", "mistral:7b"]
    selected_model = st.selectbox(
        "Ollama Model",
        model_options,
        help="Choose model based on your hardware capabilities"
    )
    
    # Update environment variable
    os.environ['OLLAMA_MODEL'] = selected_model
    
    # Advanced options
    st.subheader("Advanced Settings")
    max_iter = st.slider("Max Iterations", 1, 10, 5)
    enable_memory = st.checkbox("Enable Agent Memory", value=True)

# Main interface
st.header("Task Configuration")

# Task input
topic_input = st.text_area(
    "Enter your task or topic:",
    placeholder="e.g., Create a Python script to analyze market trends for renewable energy",
    height=100
)

# Run button
if st.button("🚀 Run Task", type="primary"):
    if not topic_input.strip():
        st.error("Please enter a topic or task.")
    else:
        with st.spinner("Initializing agents..."):
            try:
                # Import after path is set
                from open_agent_factory.crew import OpenAgentFactory
                
                # Initialize crew
                factory = OpenAgentFactory()
                crew = factory.crew()
                
                # Configure settings
                crew.max_iter = max_iter
                crew.memory = enable_memory
                
                with st.spinner("Agents are working..."):
                    # Run the crew
                    result = crew.kickoff(inputs={"topic": topic_input})
                
                # Display results
                st.success("Task completed!")
                st.subheader("Results")
                st.text_area("Agent Output", value=str(result), height=300)
                
                # Download button
                st.download_button(
                    label="Download Results",
                    data=str(result),
                    file_name="agent_results.txt",
                    mime="text/plain"
                )
                
            except ImportError as e:
                st.error(f"Import error: {e}. Make sure all dependencies are installed.")
            except Exception as e:
                st.error(f"Error running crew: {str(e)}")

# System status
st.header("System Status")

col1, col2, col3 = st.columns(3)

with col1:
    try:
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            st.success("✅ Ollama Online")
            models = response.json().get('models', [])
            st.write(f"Models: {len(models)}")
            for model in models[:3]:
                st.write(f"- {model.get('name', 'Unknown')}")
        else:
            st.error("❌ Ollama Error")
    except:
        st.error("❌ Ollama Offline")

with col2:
    try:
        chroma_host = os.getenv('CHROMA_HOST', 'localhost')
        chroma_port = int(os.getenv('CHROMA_PORT', '8000'))
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        collections = client.list_collections()
        st.success("✅ ChromaDB Online")
        st.write(f"Collections: {len(collections)}")
    except:
        st.error("❌ ChromaDB Offline")

with col3:
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(redis_url)
        r.ping()
        st.success("✅ Redis Online")
        info = r.info()
        st.write(f"Memory: {info.get('used_memory_human', 'Unknown')}")
    except:
        st.error("❌ Redis Offline")

# Footer
st.markdown("---")
st.markdown("*Built with CrewAI, Ollama, and ChromaDB • MIT License • No API keys required*")
