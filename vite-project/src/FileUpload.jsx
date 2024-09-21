import React, { useState } from 'react';
import axios from 'axios';

const FileDownload = () => {
    const [branchId, setBranchId] = useState(6); // Default branch_id
    const [error, setError] = useState(null);

    // List of all table names you want to download
    const tableNames = [
        "diagnostic_report",
        "diagnostic_report_detail",
        "diagnostic_report_diagnostic_report_detail",
        "combined_diagnostic_report",
        "combined_immunization",
        "immunization_completion",
        "immunization_recommendation",
        "immunization_report",
        "immunization_report_immunization_completion",
        "immunization_report_immunization_recommendation",
        "prescription",
        "prescription_condition",
        "prescription_medication",
        "prescription_prescription_condition",
        "prescription_prescription_medication",
        "combined_prescription",
        "patient_care_consultations",
        "patient_care_consumables",
        "patient_care_lab_tests",
        "patient_care_vaccinations",
        "patient_care_vitals",
        "patient_care",
        "combined_patient_care",
        "consultation",
        "consumables",
        "vital_info",
        "vaccination",
        "vital_detail",
        "patient_profile",
        "patient_queue",
        "patient_visit",
        "op_consultation",
        "medical_history",
        "consent_request",
        "consolidated_report",
        "discover_and_link",
        "health_professional",
        "hip_data_push_notification",
        "hip_data_push_request",
        "combined_facility"
    ];

    const handleDownloadAll = async () => {
        try {
            if (!branchId) {
                setError("Branch ID is required.");
                return;
            }

            setError(null); // Clear any previous errors

            for (const tableName of tableNames) {
                const url = `http://localhost:8000/download-csv?table_name=${tableName}&branch_id=${branchId}`;

                const response = await axios.get(url, {
                    responseType: 'blob', // Handle binary data (CSV)
                });

                // Create a download link and trigger the download for each table
                const downloadUrl = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.setAttribute('download', `${tableName}_report.csv`); // Set the CSV filename
                document.body.appendChild(link);
                link.click(); // Trigger the download
                document.body.removeChild(link); // Clean up
            }
        } catch (error) {
            console.error("Error downloading the files", error);
        }
    };

    return (
        <div>
            <h2>Download All Reports CSV</h2>

            {/* Branch ID input (required for all reports) */}
            <label>
                Branch ID:
                <input type="number" value={branchId} onChange={(e) => setBranchId(e.target.value)} />
            </label>

            {error && <p style={{ color: 'red' }}>{error}</p>}

            <button onClick={handleDownloadAll}>Download All CSVs</button>
        </div>
    );
};

export default FileDownload;
