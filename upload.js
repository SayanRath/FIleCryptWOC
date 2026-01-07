const CHUNK_SIZE = 6 * 1024 * 1024; // 6MB chunks

document.getElementById('uploadBtn').addEventListener('click', async () => {
    const fileInput = document.getElementById('fileInput');
    const statusDiv = document.getElementById('status');
    const keyContainer = document.getElementById('keyContainer');

    if (!fileInput.files.length) return alert("Select a file");
    
    const file = fileInput.files[0];
    const totalParts = Math.ceil(file.size / CHUNK_SIZE);
    
    statusDiv.innerText = "🔑 Generating Key...";
    
    // 1. Generate Master Key
    const key = await window.crypto.subtle.generateKey(
        { name: "AES-GCM", length: 256 }, true, ["encrypt", "decrypt"]
    );
    
    try {
        // 2. Start Upload (Get ID from Backend)
        const startRes = await fetch("http://127.0.0.1:8000/upload/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename: file.name, content_type: file.type })
        });
        const { upload_id, key: minioKey } = await startRes.json();
        
        const parts = []; // We need to keep track of ETags for S3

        // 3. Loop through chunks
        // 3. Loop through chunks
        for (let partNum = 1; partNum <= totalParts; partNum++) {
            const start = (partNum - 1) * CHUNK_SIZE;
            const end = Math.min(start + CHUNK_SIZE, file.size);
            const fileSlice = file.slice(start, end);
            
            statusDiv.innerText = `Encrypting & Uploading Part ${partNum} of ${totalParts}...`;

            // ... (Encryption code is fine) ... 
            const iv = window.crypto.getRandomValues(new Uint8Array(12));
            const arrayBuffer = await fileSlice.arrayBuffer();
            const encryptedContent = await window.crypto.subtle.encrypt(
                { name: "AES-GCM", iv: iv }, key, arrayBuffer
            );
            const blobToSend = new Blob([iv, encryptedContent], { type: "application/octet-stream" });

            // ... (Sign code is fine) ...
            const signRes = await fetch("http://127.0.0.1:8000/upload/sign-part", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ key: minioKey, upload_id, part_number: partNum })
            });
            const { url } = await signRes.json();

            // --- CRITICAL FIX HERE ---
            const uploadRes = await fetch(url, { method: "PUT", body: blobToSend });
            
            if (!uploadRes.ok) {
                // STOP IMMEDIATELY if MinIO rejects a chunk
                throw new Error(`Upload Failed (Part ${partNum}): ${uploadRes.statusText}`);
            }

            const etag = uploadRes.headers.get("ETag");
            if (!etag) {
                // STOP IMMEDIATELY if we can't see the ETag (CORS issue)
                throw new Error(`CORS Error: ETag header is hidden for Part ${partNum}.`);
            }
            
            // Keep quotes exactly as received
            parts.push({ PartNumber: partNum, ETag: etag });
        }

        // 4. Finish Upload
        statusDiv.innerText = "✨ Finalizing...";
        const completeRes = await fetch("http://127.0.0.1:8000/upload/complete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                key: minioKey, upload_id, parts, 
                filename: file.name, content_type: file.type 
            })
        });

        const finalData = await completeRes.json();
        
        // Show Key
        const exportedKey = await window.crypto.subtle.exportKey("jwk", key);
        document.getElementById('keyText').innerText = JSON.stringify(exportedKey);
        keyContainer.style.display = 'block';
        statusDiv.innerText = `✅ Success! File ID: ${finalData.file_id}`;

    } catch (e) {
        console.error(e);
        statusDiv.innerText = "❌ Error: " + e.message;
    }
});