const API_URL = "http://localhost:8001/api/v1/claims"; // Ensure this matches your running Backend IP/Port

// 1. Handle Form Submission
document.getElementById('claimForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const msgDiv = document.getElementById('message');
    msgDiv.textContent = "Processing...";
    msgDiv.style.color = "blue";

    // A. Gather Data
    const claimData = {
        user_id: document.getElementById('userId').value,
        policy_number: document.getElementById('policyNumber').value,
        amount: parseFloat(document.getElementById('amount').value),
        description: document.getElementById('description').value
    };

    try {
        // B. Send Metadata to Backend
        const response = await fetch(API_URL + "/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(claimData)
        });

        if (!response.ok) throw new Error("Failed to create claim metadata");
        
        const result = await response.json();
        const uploadUrl = result.s3_upload_url;
        
        // C. Upload File to S3 (if file selected)
        const fileInput = document.getElementById('file');
        if (fileInput.files.length > 0 && uploadUrl) {
            msgDiv.textContent = "Uploading document...";
            
            const uploadResponse = await fetch(uploadUrl, {
                method: "PUT",
                body: fileInput.files[0],
                headers: { "Content-Type": "application/pdf" }
            });

            if (!uploadResponse.ok) throw new Error("File upload to S3 failed");
        }

        msgDiv.textContent = "Success! Claim submitted. ID: " + result.claim_id;
        msgDiv.style.color = "green";
        loadClaims(); // Refresh list

    } catch (error) {
        console.error(error);
        msgDiv.textContent = "Error: " + error.message;
        msgDiv.style.color = "red";
    }
});

// 2. Load User History
async function loadClaims() {
    const userId = document.getElementById('userId').value;
    const listDiv = document.getElementById('claimsList');
    
    try {
        const response = await fetch(`${API_URL}/user/${userId}`);
        const claims = await response.json();
        
        if (claims.length === 0) {
            listDiv.innerHTML = "<p>No claims found.</p>";
            return;
        }

        let html = "<ul style='list-style:none; padding:0;'>";
        claims.forEach(c => {
            html += `
                <li style="border-bottom:1px solid #eee; padding:10px 0;">
                    <strong>${c.description}</strong> - $${c.amount} 
                    <span class="badge badge-${c.claim_status}">${c.claim_status}</span>
                </li>`;
        });
        html += "</ul>";
        listDiv.innerHTML = html;

    } catch (error) {
        listDiv.textContent = "Failed to load history.";
    }
}

// Load history on page load
loadClaims();
