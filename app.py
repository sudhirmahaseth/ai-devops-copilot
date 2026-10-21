import streamlit as st
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# 1. Page Configuration
st.set_page_config(
    page_title="AI DevOps Copilot",
    page_icon="🤖",
    layout="wide"
)

# 2. Main Title & Description
st.title("🤖 AI DevOps Copilot")
st.subheader("Automated Log Analysis & Infrastructure Remediation")
st.markdown("---")

# 3. Setup AI Model (Reads your API Key from Streamlit Secrets)
openai_api_key = os.environ.get("OPENAI_API_KEY")

if not openai_api_key:
    st.sidebar.warning("⚠️ Please configure your OPENAI_API_KEY in Streamlit Secrets.")
    st.info("To test locally, you can provide the API key below:")
    openai_api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")

# 4. Define Response Structure using Pydantic
class DevOpsAnalysis(BaseModel):
    root_cause: str = Field(description="The primary reason why the error occurred.")
    severity: str = Field(description="Severity level: Low, Medium, High, or Critical.")
    remediation_steps: list = Field(description="Step-by-step technical instructions to fix the issue.")
    suggested_commands: list = Field(description="Terminal or kubectl commands to debug or resolve the problem.")

# 5. Core Processing Function
def analyze_devops_logs(log_data):
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, openai_api_key=openai_api_key)
        
        parser = JsonOutputParser(pydantic_object=DevOpsAnalysis)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert AWS DevOps and Site Reliability Engineer (SRE). Analyze the provided server logs, system crashes, or Kubernetes errors. Provide a clear root cause analysis and precise remediation steps.\n{format_instructions}"),
            ("user", "Analyze the following log infrastructure data:\n\n{logs}")
        ])
        
        chain = prompt | llm | parser
        
        response = chain.invoke({
            "logs": log_data,
            "format_instructions": parser.get_format_instructions()
        })
        return response
    except Exception as e:
        st.error(f"Error communicating with AI model: {str(e)}")
        return None

# 6. Streamlit User Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📋 Paste Server / Application Logs")
    sample_log = "ERROR: connection to server at 'mariadb-cluster' failed: Connection refused\nFATAL: microservice-pod-xyz crashed with Exit Code 137\nkubelet: OOMKilled process 45821 (python)"
    
    log_input = st.text_area(
        "Input Logs here:", 
        value=sample_log, 
        height=300,
        placeholder="Paste your Kubernetes, Docker, or CloudWatch logs here..."
    )
    
    analyze_btn = st.button("🚀 Run AI Root Cause Diagnosis", type="primary")

with col2:
    st.markdown("### 🔍 AI Copilot Diagnosis")
    
    if analyze_btn:
        if not openai_api_key:
            st.error("Missing OpenAI API Key! Please supply a key to run analysis.")
        elif not log_input.strip():
            st.warning("Please paste some log data first.")
        else:
            with st.spinner("Analyzing infrastructure logs and generating solutions..."):
                result = analyze_devops_logs(log_input)
                
                if result:
                    # Display Severity Badge
                    sev = result.get('severity', 'Medium').upper()
                    if sev in ['HIGH', 'CRITICAL']:
                        st.error(f"🚨 Severity Level: {sev}")
                    else:
                        st.warning(f"⚠️ Severity Level: {sev}")
                        
                    # Display Root Cause
                    st.markdown("#### **Root Cause Analysis**")
                    st.info(result.get('root_cause'))
                    
                    # Display Remediation Steps
                    st.markdown("#### **Remediation Steps**")
                    for step in result.get('remediation_steps', []):
                        st.write(f"- {step}")
                        
                    # Display CLI Commands
                    st.markdown("#### **Suggested Execution Commands**")
                    for cmd in result.get('suggested_commands', []):
                        st.code(cmd, language="bash")
