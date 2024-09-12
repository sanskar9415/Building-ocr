import React, { useState } from 'react';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [extractedText, setExtractedText] = useState(null);
  const [extractedFormData, setExtractedFormData] = useState(null); // State for form data
  const [previewUrl, setPreviewUrl] = useState(null);
  const [averageConfidence, setAverageConfidence] = useState(null);  // New state for confidence score
  const [uploadType, setUploadType] = useState('text'); // New state for upload type (text/form)

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
    
    const endpoint = uploadType === 'form' ? 'http://localhost:8000/upload-form' : 'http://localhost:8000/upload-text';

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
          setAverageConfidence(result.average_confidence || 0);  // Set confidence score
        } else {
          setExtractedFormData(result.form_data || {});
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
          <h4>Confidence Score: {averageConfidence}%</h4>  {/* Display confidence score */}
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
    </div>
  );
};

export default FileUpload;
