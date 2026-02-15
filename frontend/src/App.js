import React, { useState } from 'react';
import './App.css';


function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setError(null);
    setLoading(true);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload first');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:5000/api/analyze', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();

      if (response.ok) {
        setResult(data);
      } else {
        setError(data.error || "Something went wrong on the server.");
      }
    } catch (err) {
      setError("Failed to connect to the server. Is the Flask backend running?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📑 AI Consumer Advocate</h1>
        <p>Upload a loan agreement or insurance policy to detect hidden risks.</p>
      </header>

      <main className="container">
        <div className="upload-box">
          <input 
            type="file" 
            accept=".pdf" 
            onChange={handleFileChange} 
            id="file-upload" 
          />
          <label htmlFor="file-upload" className="custom-file-upload">
            {file ? file.name : "Choose PDF Contract"}
          </label>

          <button 
            onClick={handleUpload} 
            disabled={loading || !file}
            className="analyze-btn"
          >
            {loading ? "Analyzing..." : "Analyze Risk"}
          </button>
        </div>

        {error && <div className="error-box">⚠️ {error}</div>}

        {result && (
          <div className={`result-box ${result.risk_level.toLowerCase()}`}>
            <h2>Risk Score: {result.risk_score}/100</h2>
            <div className="badge">{result.risk_level} RISK</div>
            
            <h3>Why?</h3>
            <p>{result.explanation}</p>
            
            <div className="details">
              <small>Analyzed file: {result.filename}</small>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

  
  
  


export default App;