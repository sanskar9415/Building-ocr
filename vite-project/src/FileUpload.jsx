import React, { useState } from 'react';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [extractedText, setExtractedText] = useState(null);
  const [extractedFormData, setExtractedFormData] = useState(null); 
  const [summaryAndMedicines, setSummaryAndMedicines] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [averageConfidence, setAverageConfidence] = useState(null);  
  const [uploadType, setUploadType] = useState('text');

  const supportedFormats = ['image/jpeg', 'image/png', 'application/pdf', 'image/tiff'];

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    
    if (selectedFile && supportedFormats.includes(selectedFile.type)) {
      setFile(selectedFile);
      setError(null);
      
      const fileUrl = URL.createObjectURL(selectedFile);
      setPreviewUrl(fileUrl);
    } else {
      setError('Unsupported file format. Please upload a JPEG, PNG, PDF, or TIFF file.');
      setFile(null);
      setPreviewUrl(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
  
    if (!file) {
      setError('Please upload a valid file.');
      return;
    }
  
    const formData = new FormData();
    formData.append('file', file);
    
    let endpoint;
    if (uploadType === 'form') {
      endpoint = 'http://localhost:8000/upload-form';
    } else if (uploadType === 'ai') {
      endpoint = 'http://localhost:8000/extract-info';
    } else {
      endpoint = 'http://localhost:8000/upload-text';
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });
  
      const result = await response.json();
      if (response.ok) {
        setSuccessMessage(`File uploaded successfully.`);
        
        if (uploadType === 'text') {
          setExtractedText(result.extracted_text || "No text extracted.");
          setAverageConfidence(result.average_confidence || 0); 
        } else if (uploadType === 'form') {
          setExtractedFormData(result.form_data || {});
        } else if (uploadType === 'ai') {
          setSummaryAndMedicines(result.summary_and_medicines || { summary: "No summary", medicines: [] });
        }

        setFile(null);
        setPreviewUrl(null);
      } else {
        setError(result.detail || 'Error uploading file');
      }
    } catch (err) {
      setError('Error uploading file');
      console.error('Error uploading file', err);
    }
  };

  return (
    <div className="file-upload">
      <h2>Upload a Document</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>
            <input 
              type="radio" 
              name="uploadType" 
              value="text" 
              checked={uploadType === 'text'}
              onChange={() => setUploadType('text')} 
            /> 
            Extract Text
          </label>
          <label>
            <input 
              type="radio" 
              name="uploadType" 
              value="form" 
              checked={uploadType === 'form'}
              onChange={() => setUploadType('form')} 
            /> 
            Extract Form Data
          </label>
          <label>
            <input 
              type="radio" 
              name="uploadType" 
              value="ai" 
              checked={uploadType === 'ai'}
              onChange={() => setUploadType('ai')} 
            /> 
            AI-based Analysis
          </label>
        </div>
        <input 
          type="file" 
          accept=".jpeg,.jpg,.png,.pdf,.tiff"
          onChange={handleFileChange}
        />
        {error && <p style={{ color: 'red' }}>{error}</p>}
        {successMessage && <p style={{ color: 'green' }}>{successMessage}</p>}
        <button type="submit" disabled={!file}>Upload</button>
      </form>
      {previewUrl && (
        <div>
          <h3>File Preview:</h3>
          {file.type.startsWith('image/') && (
            <img src={previewUrl} alt="Preview" style={{ maxWidth: '100%', maxHeight: '400px' }} />
          )}
          {file.type === 'application/pdf' && (
            <iframe src={previewUrl} style={{ width: '100%', height: '400px' }}></iframe>
          )}
        </div>
      )}
      {extractedText && (
        <div>
          <h3>Extracted Text:</h3>
          <p>{extractedText}</p>
          <h4>Confidence Score: {averageConfidence}%</h4>
        </div>
      )}
      {extractedFormData && (
        <div>
          <h3>Extracted Form Data:</h3>
          <ul>
            {Object.entries(extractedFormData).map(([key, value], index) => (
              <li key={index}>
                <strong>{key}:</strong> {value}
              </li>
            ))}
          </ul>
        </div>
      )}
      {summaryAndMedicines && (
  <div>
    <h3>AI-based Summary:</h3>
    <p>{summaryAndMedicines.summary}</p>
    
    <h3>Medicines Identified:</h3>
    <ul>
      {Array.isArray(summaryAndMedicines.medicines) && summaryAndMedicines.medicines.length > 0 ? (
        summaryAndMedicines.medicines.map((medicine, index) => (
          <li key={index}>{medicine}</li>
        ))
      ) : (
        <p>No medicines identified or data is not in expected format.</p>
      )}
    </ul>
  </div>
)}
    </div>
  );
};

export default FileUpload;
