import React, { useState } from 'react';
import axios from 'axios';

const FileDownload = () => {
    const [tableName, setTableName] = useState('diagnostic_report');
    const [branchId, setBranchId] = useState(6);  // Default branch_id, can be set dynamically
    const [error, setError] = useState(null);

    const handleDownload = async () => {
        try {
            if (!branchId) {
                setError("Branch ID is required.");
                return;
            }

            setError(null); // Clear any previous errors

            // Construct the URL with branch_id (facility_id will be handled in the backend)
            const url = `http://localhost:8000/download-csv?table_name=${tableName}&branch_id=${branchId}`;

            const response = await axios.get(url, {
                responseType: 'blob', // Important for handling binary data (CSV)
            });

            const downloadUrl = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = downloadUrl;
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
                    <option value="prescription">prescription</option>
                    <option value="prescription_condition">prescription_condition</option>
                    <option value="prescription_medication">prescription_medication</option>
                    <option value="prescription_prescription_condition">prescription_prescription_condition</option>
                    <option value="prescription_prescription_medication">prescription_prescription_medication</option>
                    <option value="patient_care_consultations">patient_care_consultations</option>
                    <option value="patient_care_consumables">patient_care_consumables</option>
                    <option value="patient_care_lab_tests">patient_care_lab_tests</option>
                    <option value="patient_care_vaccinations">patient_care_vaccinations</option>
                    <option value="patient_care_vitals">patient_care_vitals</option>
                    <option value="combined_diagnostic_report">Combined Diagnostic Report</option>
                    <option value="combined_immunization">Immunization Report</option>
                    <option value="patient_care">Patient Care</option>
                    <option value="combined_patient_care">Combined Patient Care</option>
                    <option value="combined_prescription">Combined Prescription</option>
                    <option value="combined_facility">Combined Facility</option>
                </select>
            </label>

            {/* Branch ID input (required for all reports) */}
            <label>
                Branch ID:
                <input type="number" value={branchId} onChange={(e) => setBranchId(e.target.value)} />
            </label>

            {error && <p style={{ color: 'red' }}>{error}</p>}

            <button onClick={handleDownload}>Download CSV</button>
        </div>
    );
};

export default FileDownload;
