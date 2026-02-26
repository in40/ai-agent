"""
Smart Ingestion and Jobs Management Tabs for RAG System
"""
import streamlit as st
import requests
import json
import os
from pathlib import Path
import tempfile

# RAG Service configuration
RAG_SERVICE_URL = os.getenv('RAG_SERVICE_URL', 'http://localhost:5003')
DOCUMENT_STORE_URL = os.getenv('DOCUMENT_STORE_URL', 'http://localhost:3070')


def create_smart_ingestion_tab():
    """Create the Smart Ingestion tab"""
    st.header("📚 Smart Ingestion")
    st.markdown("""
    Upload and process documents using AI-powered smart chunking.
    Documents are automatically split into semantic chunks optimized for RAG.
    """)
    
    # Create sub-tabs for different ingestion methods
    ingest_tab1, ingest_tab2, ingest_tab3 = st.tabs(["Upload Files", "Document Store", "Batch Processing"])
    
    with ingest_tab1:
        st.subheader("Upload Files for Smart Ingestion")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Upload PDF, TXT, or MD files",
            type=['pdf', 'txt', 'md'],
            accept_multiple_files=True,
            key="smart_ingest_uploader"
        )
        
        # Ingestion options
        st.subheader("Ingestion Options")
        
        chunking_strategy = st.selectbox(
            "Chunking Strategy",
            options=["smart_chunking", "naive_chunking", "section_based"],
            help="Smart chunking uses LLM to preserve semantic units"
        )
        
        ingest_chunks = st.checkbox("Ingest chunks into vector DB", value=True)
        
        custom_prompt = st.text_area(
            "Custom Chunking Prompt (optional)",
            help="Override the default chunking prompt",
            height=100
        )
        
        # Start ingestion button
        if st.button("🚀 Start Smart Ingestion", type="primary"):
            if not uploaded_files:
                st.warning("Please upload at least one file")
            else:
                try:
                    # Prepare files for upload
                    files = []
                    for uploaded_file in uploaded_files:
                        files.append(('files', (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)))
                    
                    # Prepare parameters
                    params = {
                        'chunking_strategy': chunking_strategy,
                        'ingest_chunks': ingest_chunks,
                        'custom_prompt': custom_prompt if custom_prompt else None
                    }
                    
                    # Show progress
                    with st.spinner(f"Uploading {len(uploaded_files)} file(s) for smart ingestion..."):
                        # Call the RAG service ingest endpoint
                        response = requests.post(
                            f"{RAG_SERVICE_URL}/ingest",
                            files=files,
                            data=params,
                            timeout=300
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ Smart ingestion completed successfully!")
                            
                            # Display results
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Documents Processed", result.get('documents_processed', 0))
                            with col2:
                                st.metric("Chunks Generated", result.get('total_chunks', 0))
                            with col3:
                                st.metric("Job ID", result.get('job_id', 'N/A')[:20] + '...')
                            
                            # Show detailed results
                            with st.expander("View Detailed Results"):
                                st.json(result)
                        else:
                            st.error(f"❌ Ingestion failed: {response.status_code}")
                            st.error(response.text)
                            
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to RAG service. Is it running on port 5003?")
                except Exception as e:
                    st.error(f"❌ Error during ingestion: {str(e)}")
    
    with ingest_tab2:
        st.subheader("📦 Document Store Integration")
        st.markdown("""
        Import documents from the Document Store MCP Server.
        Select documents from existing ingestion jobs.
        """)
        
        # Try to fetch jobs from Document Store
        if st.button("🔄 Fetch Document Store Jobs"):
            try:
                # Call document store jobs endpoint
                response = requests.get(
                    f"{RAG_SERVICE_URL}/api/rag/document_store/jobs",
                    timeout=10
                )
                
                if response.status_code == 200:
                    jobs = response.json().get('jobs', [])
                    
                    if jobs:
                        st.success(f"Found {len(jobs)} job(s) in Document Store")
                        
                        # Create job selector
                        job_options = {f"{job.get('job_id', 'unknown')[:20]}... ({job.get('document_count', 0)} docs)": job for job in jobs}
                        selected_job_label = st.selectbox("Select Job", options=list(job_options.keys()))
                        
                        if selected_job_label:
                            selected_job = job_options[selected_job_label]
                            st.write(f"**Job ID:** {selected_job.get('job_id')}")
                            st.write(f"**Documents:** {selected_job.get('document_count', 0)}")
                            st.write(f"**Created:** {selected_job.get('created_at', 'N/A')}")
                            
                            # Show documents in job
                            if 'documents' in selected_job:
                                st.write("**Documents in this job:**")
                                for doc in selected_job['documents']:
                                    st.write(f"- {doc.get('filename', 'unknown')} ({doc.get('format', 'unknown')})")
                            
                            # Import button
                            if st.button("📥 Import Selected Documents"):
                                try:
                                    # Call import endpoint
                                    import_response = requests.post(
                                        f"{RAG_SERVICE_URL}/import_from_document_store",
                                        json={'job_id': selected_job.get('job_id')},
                                        timeout=300
                                    )
                                    
                                    if import_response.status_code == 200:
                                        result = import_response.json()
                                        st.success("✅ Documents imported successfully!")
                                        st.json(result)
                                    else:
                                        st.error(f"❌ Import failed: {import_response.status_code}")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error during import: {str(e)}")
                    else:
                        st.info("No jobs found in Document Store")
                else:
                    st.error(f"❌ Failed to fetch jobs: {response.status_code}")
                    st.info("Make sure Document Store MCP Server is running on port 3070")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to Document Store. Is it running on port 3070?")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        # Show info about Document Store
        with st.expander("ℹ️ About Document Store"):
            st.markdown("""
            The Document Store MCP Server manages document ingestion jobs.
            
            **To use Document Store:**
            1. Make sure the Document Store MCP Server is running on port 3070
            2. Documents should be uploaded to the Document Store first
            3. Select a job and import documents for RAG processing
            
            **Starting Document Store:**
            ```bash
            cd /root/qwen/ai_agent/document-store-mcp-server
            python -m document_store_server.server --port 3070
            ```
            """)
    
    with ingest_tab3:
        st.subheader("📊 Batch Processing")
        st.markdown("""
        Process multiple documents in batch mode.
        Useful for large-scale document ingestion.
        """)
        
        # Directory selector
        source_directory = st.text_input(
            "Source Directory",
            value="/root/qwen/ai_agent/downloads",
            help="Directory containing PDF files to process"
        )
        
        # Batch options
        max_files = st.number_input(
            "Maximum files to process",
            min_value=1,
            max_value=1000,
            value=50
        )
        
        parallel_processing = st.checkbox("Enable parallel processing", value=False)
        
        if st.button("🚀 Start Batch Processing"):
            if not os.path.exists(source_directory):
                st.error(f"❌ Directory does not exist: {source_directory}")
            else:
                # Count PDF files
                pdf_files = [f for f in os.listdir(source_directory) if f.endswith('.pdf')]
                st.info(f"Found {len(pdf_files)} PDF files in directory")
                
                if pdf_files:
                    try:
                        # Call batch processing endpoint
                        response = requests.post(
                            f"{RAG_SERVICE_URL}/batch_ingest",
                            json={
                                'directory': source_directory,
                                'max_files': max_files,
                                'parallel': parallel_processing
                            },
                            timeout=600
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ Batch processing completed!")
                            st.json(result)
                        else:
                            st.error(f"❌ Batch processing failed: {response.status_code}")
                            
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")


def create_jobs_tab():
    """Create the Jobs Management tab"""
    st.header("💼 Jobs Management")
    st.markdown("""
    View and manage background processing jobs.
    Monitor progress, retry failed jobs, and view results.
    """)
    
    # Jobs action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Jobs", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Completed", use_container_width=True):
            st.info("Clear completed jobs functionality - to be implemented")
    
    with col3:
        if st.button("📊 View Statistics", use_container_width=True):
            st.info("Job statistics - to be implemented")
    
    # Fetch and display jobs
    try:
        # Call jobs endpoint
        response = requests.get(
            f"{RAG_SERVICE_URL}/jobs",
            timeout=10
        )
        
        if response.status_code == 200:
            jobs = response.json().get('jobs', [])
            
            if jobs:
                # Display job count
                st.subheader(f"Jobs ({len(jobs)} total)")
                
                # Filter options
                filter_col1, filter_col2 = st.columns(2)
                with filter_col1:
                    status_filter = st.selectbox(
                        "Filter by Status",
                        options=["All", "pending", "processing", "completed", "failed", "cancelled"]
                    )
                
                # Filter jobs by status
                if status_filter != "All":
                    filtered_jobs = [j for j in jobs if j.get('status') == status_filter]
                else:
                    filtered_jobs = jobs
                
                st.write(f"Showing {len(filtered_jobs)} job(s)")
                
                # Display jobs
                for job in filtered_jobs:
                    with st.expander(
                        f"{'✅' if job.get('status') == 'completed' else '⏳' if job.get('status') == 'processing' else '⚠️' if job.get('status') == 'failed' else '📋'} "
                        f"Job: {job.get('job_id', 'unknown')[:30]}... "
                        f"({job.get('status', 'unknown')})"
                    ):
                        # Job details
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Status", job.get('status', 'unknown'))
                        with col2:
                            st.metric("Type", job.get('job_type', 'unknown'))
                        with col3:
                            created_at = job.get('created_at', 'N/A')
                            if created_at != 'N/A':
                                created_at = created_at[:19]  # Trim timestamp
                            st.metric("Created", created_at)
                        with col4:
                            chunks = job.get('chunks_generated', 0)
                            st.metric("Chunks", chunks)
                        
                        # Progress bar for processing jobs
                        if job.get('status') == 'processing':
                            total = job.get('total_documents', 1)
                            processed = job.get('processed_documents', 0)
                            progress = processed / total if total > 0 else 0
                            st.progress(progress)
                            st.write(f"{processed}/{total} documents processed")
                        
                        # Job parameters
                        if 'parameters' in job:
                            with st.expander("View Parameters"):
                                st.json(job.get('parameters', {}))
                        
                        # Error message if failed
                        if job.get('status') == 'failed' and job.get('error'):
                            st.error(f"**Error:** {job.get('error')}")
                        
                        # Action buttons
                        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                        
                        with action_col1:
                            if job.get('status') == 'pending':
                                if st.button("▶️ Start", key=f"start_{job.get('job_id')}"):
                                    try:
                                        resp = requests.post(
                                            f"{RAG_SERVICE_URL}/jobs/{job.get('job_id')}/start_processing",
                                            timeout=30
                                        )
                                        if resp.status_code == 200:
                                            st.success("Job started!")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to start: {resp.status_code}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                        
                        with action_col2:
                            if job.get('status') in ['failed', 'cancelled']:
                                if st.button("🔄 Retry", key=f"retry_{job.get('job_id')}"):
                                    try:
                                        resp = requests.post(
                                            f"{RAG_SERVICE_URL}/jobs/{job.get('job_id')}/retry",
                                            timeout=30
                                        )
                                        if resp.status_code == 200:
                                            st.success("Job retry initiated!")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to retry: {resp.status_code}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                        
                        with action_col3:
                            if job.get('status') == 'processing':
                                if st.button("⏸️ Cancel", key=f"cancel_{job.get('job_id')}"):
                                    try:
                                        resp = requests.post(
                                            f"{RAG_SERVICE_URL}/jobs/{job.get('job_id')}/cancel",
                                            timeout=30
                                        )
                                        if resp.status_code == 200:
                                            st.success("Job cancelled!")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to cancel: {resp.status_code}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                        
                        with action_col4:
                            if st.button("🗑️ Delete", key=f"delete_{job.get('job_id')}"):
                                try:
                                    resp = requests.delete(
                                        f"{RAG_SERVICE_URL}/jobs/{job.get('job_id')}/delete",
                                        timeout=30
                                    )
                                    if resp.status_code == 200:
                                        st.success("Job deleted!")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to delete: {resp.status_code}")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        
                        # View logs button
                        if st.button("📋 View Logs", key=f"logs_{job.get('job_id')}"):
                            with st.expander("Job Logs"):
                                # Get job logs (to be implemented)
                                st.info("Job logs - to be implemented")
            else:
                st.info("No jobs found")
        else:
            st.error(f"❌ Failed to fetch jobs: {response.status_code}")
            st.info("Make sure the RAG service is running on port 5003")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to RAG service. Is it running on port 5003?")
    except Exception as e:
        st.error(f"❌ Error fetching jobs: {str(e)}")
    
    # Job statistics section
    st.divider()
    st.subheader("📈 Job Statistics")
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    try:
        response = requests.get(f"{RAG_SERVICE_URL}/jobs", timeout=10)
        if response.status_code == 200:
            jobs = response.json().get('jobs', [])
            
            # Calculate statistics
            total_jobs = len(jobs)
            completed_jobs = len([j for j in jobs if j.get('status') == 'completed'])
            failed_jobs = len([j for j in jobs if j.get('status') == 'failed'])
            pending_jobs = len([j for j in jobs if j.get('status') == 'pending'])
            
            with stat_col1:
                st.metric("Total Jobs", total_jobs)
            with stat_col2:
                st.metric("Completed", completed_jobs)
            with stat_col3:
                st.metric("Failed", failed_jobs)
            with stat_col4:
                st.metric("Pending", pending_jobs)
    except:
        with stat_col1:
            st.metric("Total", "N/A")
        with stat_col2:
            st.metric("Completed", "N/A")
        with stat_col3:
            st.metric("Failed", "N/A")
        with stat_col4:
            st.metric("Pending", "N/A")


def create_rag_settings_tab():
    """Create RAG Settings tab"""
    st.header("⚙️ RAG Settings")
    st.markdown("""
    Configure RAG service settings and connections.
    """)
    
    # Service URLs
    st.subheader("Service URLs")
    
    rag_url = st.text_input("RAG Service URL", value=RAG_SERVICE_URL)
    doc_store_url = st.text_input("Document Store URL", value=DOCUMENT_STORE_URL)
    
    # Test connections
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Test RAG Connection"):
            try:
                response = requests.get(f"{rag_url}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ RAG service is healthy")
                    st.json(response.json())
                else:
                    st.error(f"❌ RAG service returned: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Cannot connect to RAG service: {str(e)}")
    
    with col2:
        if st.button("Test Document Store Connection"):
            try:
                response = requests.get(f"{doc_store_url}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ Document Store is healthy")
                    st.json(response.json())
                else:
                    st.error(f"❌ Document Store returned: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Cannot connect to Document Store: {str(e)}")
    
    # Configuration info
    with st.expander("ℹ️ Environment Variables"):
        st.markdown("""
        Configure these environment variables:
        
        ```bash
        export RAG_SERVICE_URL=http://localhost:5003
        export DOCUMENT_STORE_URL=http://localhost:3070
        ```
        
        Or add them to your `.env` file.
        """)
