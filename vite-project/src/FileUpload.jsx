import React, { useState } from 'react';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [extractedText, setExtractedText] = useState(null);


  const supportedFormats = ['image/jpeg', 'image/png', 'application/pdf', 'image/tiff'];

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    
    if (selectedFile && supportedFormats.includes(selectedFile.type)) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Unsupported file format. Please upload a JPEG, PNG, PDF, or TIFF file.');
      setFile(null);
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
  
    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
  
      const result = await response.json();
      if (response.ok) {
        setSuccessMessage(`File uploaded successfully: ${result.file_name}`);
        setExtractedText(result.extracted_text); // Display extracted text
        setFile(null);  // Clear the file input
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
        <input 
          type="file" 
          accept=".jpeg,.jpg,.png,.pdf,.tiff"
          onChange={handleFileChange}
        />
        {error && <p style={{ color: 'red' }}>{error}</p>}
        {successMessage && <p style={{ color: 'green' }}>{successMessage}</p>}
        <button type="submit" disabled={!file}>Upload</button>
      </form>
      {extractedText && (
  <div>
    <h3>Extracted Text:</h3>
    <p>{extractedText}</p>
  </div>
)}

    </div>
  );
};

export default FileUpload;
