import React, { useState } from 'react';
import axios from 'axios';

const FileDownload = () => {
    const [tableName, setTableName] = useState('diagnostic_report');

    const handleDownload = async () => {
        try {
            const branch_id = 6; // Hardcoded branch_id for now
            const response = await axios.get(`http://localhost:8000/download-csv?table_name=${tableName}&branch_id=${branch_id}`, {
                responseType: 'blob', // Important for handling binary data (CSV)
            });

            // Create a blob link to download the CSV 
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${tableName}_report.csv`); // CSV filename
            document.body.appendChild(link);
            link.click(); // Trigger the download
            document.body.removeChild(link); // Clean up
        } catch (error) {
            console.error("Error downloading the file", error);
        }
    };

    return (
        <div>
            <h2>Download Report CSV</h2>
            <label>
                Select Table:
                <select value={tableName} onChange={(e) => setTableName(e.target.value)}>
                    <option value="diagnostic_report">Diagnostic Report</option>
                    <option value="combined_diagnostic_report">Combined Diagnostic Report</option>
                    <option value="combined_immunization">Immunization Report</option>
                    <option value="patient_care">Patient Care</option>
                    <option value="combined_patient_care">Combined Patient Care</option>
                    {/* Add more options for each table */}
                </select>
            </label>
            <button onClick={handleDownload}>Download CSV</button>
        </div>
    );
};

export default FileDownload;
