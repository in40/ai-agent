import React, { useState, useCallback } from 'react';

const RAGComponent = () => {
  const [activeTab, setActiveTab] = useState('query'); // 'query', 'ingest', 'retrieve'
  const [query, setQuery] = useState('');
  const [filePaths, setFilePaths] = useState('');
  const [topK, setTopK] = useState(5);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Function to get API URL
  const getApiUrl = () => {
    let apiUrl = process.env.REACT_APP_API_URL;

    if (!apiUrl) {
      const currentHost = window.location.hostname;
      if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
        apiUrl = 'http://192.168.51.138:5000';  // Changed from 5001 to 5000 (gateway service)
      } else {
        apiUrl = `http://${currentHost}:5000`;  // Changed from 5001 to 5000 (gateway service)
      }
    }

    return apiUrl;
  };

  // Function to handle RAG query
  const handleQuery = async () => {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);

    try {
      const response = await fetch(`${getApiUrl()}/api/rag/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`Query failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Function to handle document ingestion
  const handleIngest = async () => {
    if (!filePaths.trim()) {
      setError('Please enter file paths (comma-separated)');
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);

    try {
      const pathsArray = filePaths.split(',').map(path => path.trim()).filter(path => path);
      
      const response = await fetch(`${getApiUrl()}/api/rag/ingest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ file_paths: pathsArray }),
      });

      if (!response.ok) {
        throw new Error(`Ingestion failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Function to handle document retrieval
  const handleRetrieve = async () => {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);

    try {
      const response = await fetch(`${getApiUrl()}/api/rag/retrieve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, top_k: parseInt(topK) }),
      });

      if (!response.ok) {
        throw new Error(`Retrieval failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Render results based on active tab
  const renderResults = () => {
    if (!results) return null;

    if (activeTab === 'query') {
      return (
        <div className="results-container">
          <h3>Response</h3>
          <div className="result-content">
            <p><strong>Answer:</strong> {results.response || 'N/A'}</p>
            {results.context && (
              <div>
                <p><strong>Context:</strong></p>
                <pre>{JSON.stringify(results.context, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      );
    } else if (activeTab === 'retrieve') {
      return (
        <div className="results-container">
          <h3>Retrieved Documents</h3>
          <div className="result-content">
            {results.documents && results.documents.length > 0 ? (
              <ul>
                {results.documents.map((doc, index) => (
                  <li key={index}>
                    <p><strong>Document {index + 1}:</strong></p>
                    <p>Content: {doc.page_content.substring(0, 200)}...</p>
                    <p>Source: {doc.metadata?.source || 'Unknown'}</p>
                    <hr />
                  </li>
                ))}
              </ul>
            ) : (
              <p>No documents found.</p>
            )}
          </div>
        </div>
      );
    } else {
      return (
        <div className="results-container">
          <h3>Status</h3>
          <div className="result-content">
            <p>{results.message || 'Operation completed'}</p>
          </div>
        </div>
      );
    }
  };

  return (
    <div className="rag-component">
      <h2>RAG Functions</h2>
      
      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button 
          className={`tab-button ${activeTab === 'query' ? 'active' : ''}`}
          onClick={() => setActiveTab('query')}
        >
          Query
        </button>
        <button 
          className={`tab-button ${activeTab === 'ingest' ? 'active' : ''}`}
          onClick={() => setActiveTab('ingest')}
        >
          Ingest Documents
        </button>
        <button 
          className={`tab-button ${activeTab === 'retrieve' ? 'active' : ''}`}
          onClick={() => setActiveTab('retrieve')}
        >
          Retrieve Documents
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* Query Tab */}
        {activeTab === 'query' && (
          <div className="query-tab">
            <div className="input-group">
              <label htmlFor="query-input">Enter your query:</label>
              <textarea
                id="query-input"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a question about your documents..."
                rows="3"
              />
            </div>
            <button onClick={handleQuery} disabled={loading}>
              {loading ? 'Processing...' : 'Submit Query'}
            </button>
          </div>
        )}

        {/* Ingest Tab */}
        {activeTab === 'ingest' && (
          <div className="ingest-tab">
            <div className="input-group">
              <label htmlFor="file-paths">Enter file paths (comma-separated):</label>
              <textarea
                id="file-paths"
                value={filePaths}
                onChange={(e) => setFilePaths(e.target.value)}
                placeholder="/path/to/doc1.pdf, /path/to/doc2.txt, /path/to/doc3.docx"
                rows="3"
              />
            </div>
            <button onClick={handleIngest} disabled={loading}>
              {loading ? 'Processing...' : 'Ingest Documents'}
            </button>
          </div>
        )}

        {/* Retrieve Tab */}
        {activeTab === 'retrieve' && (
          <div className="retrieve-tab">
            <div className="input-group">
              <label htmlFor="retrieve-query">Enter your query:</label>
              <textarea
                id="retrieve-query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search for documents..."
                rows="3"
              />
            </div>
            <div className="input-group">
              <label htmlFor="top-k">Number of results (top_k):</label>
              <input
                id="top-k"
                type="number"
                value={topK}
                onChange={(e) => setTopK(e.target.value)}
                min="1"
                max="100"
              />
            </div>
            <button onClick={handleRetrieve} disabled={loading}>
              {loading ? 'Processing...' : 'Retrieve Documents'}
            </button>
          </div>
        )}
      </div>

      {/* Results Section */}
      {error && (
        <div className="error-message">
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}

      {loading && (
        <div className="loading">
          <p>Processing...</p>
        </div>
      )}

      {results && !loading && renderResults()}
    </div>
  );
};

export default RAGComponent;