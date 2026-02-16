import React, { useState } from 'react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Hardcoded 127.0.0.1 for safety
      const response = await fetch('http://127.0.0.1:5000/api/analyze', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
      } else {
        setError(data.error || "Server error");
      }
    } catch (err) {
      console.error(err);
      setError("Failed to connect. Make sure Backend is running!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📑 AI Consumer Advocate</h1>
      </header>
      <main className="container">
        
        <div className="upload-box">
          {/* 1. The Hidden Input (We hide the ugly default) */}
          <input 
            type="file" 
            id="file-upload" 
            onChange={handleFileChange} 
            accept=".pdf" 
            style={{ display: 'none' }} 
          />

          {/* 2. The Custom Button (Visible) */}
          <label htmlFor="file-upload" className="custom-file-upload">
            {file ? `📄 ${file.name}` : "📂 Click to Select PDF"}
          </label>

          {/* 3. The Analyze Button */}
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
          <div className="result-box">
            <h2>Risk Score: {result.risk_score}/100 ({result.risk_level})</h2>
            <p>{result.explanation}</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;