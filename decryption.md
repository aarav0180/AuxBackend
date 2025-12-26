# VibeSync API Response Decryption Guide

All API responses are encrypted using **AES-256-CBC** encryption for security. This guide will help you decrypt the responses.

---

## 🔐 Encryption Details

- **Algorithm**: AES-256-CBC (Advanced Encryption Standard)
- **Key Size**: 256 bits (32 bytes)
- **Block Size**: 128 bits (16 bytes)
- **Mode**: CBC (Cipher Block Chaining)
- **Padding**: PKCS7
- **Encoding**: Base64

---

## 🔑 Encryption Key

```
VibeSync2025SecureKey1234567890X
```

**Important**: This key must be kept secret in production environments. Store it in environment variables.

---

## 📦 Encrypted Response Format

All API responses are returned in this format:

```json
{
  "encrypted": true,
  "algorithm": "AES-256-CBC",
  "data": "base64_encoded_encrypted_data_here",
  "iv": "base64_encoded_initialization_vector_here",
  "encoding": "base64"
}
```

**Fields**:
- `encrypted`: Always `true` for encrypted responses
- `algorithm`: Encryption algorithm used
- `data`: Base64-encoded encrypted JSON data
- `iv`: Base64-encoded initialization vector (required for decryption)
- `encoding`: Encoding format (base64)

---

## 🔓 Decryption Methods

### Method 1: Python (Recommended)

```python
import base64
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

def decrypt_response(encrypted_data: str, iv: str) -> dict:
    """
    Decrypt an encrypted API response.
    
    Args:
        encrypted_data: Base64-encoded encrypted data
        iv: Base64-encoded initialization vector
        
    Returns:
        Decrypted dictionary
    """
    # Encryption key
    key = b'VibeSync2025SecureKey1234567890X'
    
    # Decode from base64
    encrypted_bytes = base64.b64decode(encrypted_data)
    iv_bytes = base64.b64decode(iv)
    
    # Create cipher and decrypt
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv_bytes),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()
    
    # Unpad the data
    unpadder = padding.PKCS7(128).unpadder()
    json_bytes = unpadder.update(padded_data) + unpadder.finalize()
    
    # Convert back to dictionary
    json_str = json_bytes.decode('utf-8')
    return json.loads(json_str)

# Example usage
response = {
    "encrypted": True,
    "algorithm": "AES-256-CBC",
    "data": "your_encrypted_data_here",
    "iv": "your_iv_here",
    "encoding": "base64"
}

decrypted = decrypt_response(response["data"], response["iv"])
print(json.dumps(decrypted, indent=2))
```

---

### Method 2: JavaScript/Node.js

```javascript
const crypto = require('crypto');

function decryptResponse(encryptedData, iv) {
    // Encryption key
    const key = Buffer.from('VibeSync2025SecureKey1234567890X', 'utf-8');
    
    // Decode from base64
    const encryptedBuffer = Buffer.from(encryptedData, 'base64');
    const ivBuffer = Buffer.from(iv, 'base64');
    
    // Create decipher
    const decipher = crypto.createDecipheriv('aes-256-cbc', key, ivBuffer);
    
    // Decrypt
    let decrypted = decipher.update(encryptedBuffer);
    decrypted = Buffer.concat([decrypted, decipher.final()]);
    
    // Parse JSON
    return JSON.parse(decrypted.toString('utf-8'));
}

// Example usage
const response = {
    encrypted: true,
    algorithm: "AES-256-CBC",
    data: "your_encrypted_data_here",
    iv: "your_iv_here",
    encoding: "base64"
};

const decrypted = decryptResponse(response.data, response.iv);
console.log(JSON.stringify(decrypted, null, 2));
```

---

### Method 3: OpenSSL Command Line

```bash
# Save encrypted data to file
echo "base64_encrypted_data" | base64 -d > encrypted.bin

# Decrypt using OpenSSL
openssl enc -d -aes-256-cbc \
  -K $(echo -n "VibeSync2025SecureKey1234567890X" | xxd -p) \
  -iv $(echo "base64_iv" | base64 -d | xxd -p) \
  -in encrypted.bin \
  -out decrypted.json

# View decrypted JSON
cat decrypted.json | jq .
```

---

### Method 4: PHP

```php
<?php
function decryptResponse($encryptedData, $iv) {
    // Encryption key
    $key = 'VibeSync2025SecureKey1234567890X';
    
    // Decode from base64
    $encrypted = base64_decode($encryptedData);
    $ivDecoded = base64_decode($iv);
    
    // Decrypt
    $decrypted = openssl_decrypt(
        $encrypted,
        'aes-256-cbc',
        $key,
        OPENSSL_RAW_DATA,
        $ivDecoded
    );
    
    // Parse JSON
    return json_decode($decrypted, true);
}

// Example usage
$response = [
    'encrypted' => true,
    'algorithm' => 'AES-256-CBC',
    'data' => 'your_encrypted_data_here',
    'iv' => 'your_iv_here',
    'encoding' => 'base64'
];

$decrypted = decryptResponse($response['data'], $response['iv']);
print_r($decrypted);
?>
```

---

## 🛠️ Complete Example

### Step 1: Make an API Request

```bash
curl -X GET "http://localhost:8000/rooms/ABC123"
```

### Step 2: You'll Receive an Encrypted Response

```json
{
  "encrypted": true,
  "algorithm": "AES-256-CBC",
  "data": "kJ8NHLXqR9+vK2mPl4YzTw==...",
  "iv": "xYz7pLm4nB3wQ1vK8hG2fA==",
  "encoding": "base64"
}
```

### Step 3: Decrypt Using Python

```python
import requests
import base64
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

# Make API request
response = requests.get("http://localhost:8000/rooms/ABC123")
encrypted_response = response.json()

# Decrypt
key = b'VibeSync2025SecureKey1234567890X'
encrypted_data = base64.b64decode(encrypted_response["data"])
iv = base64.b64decode(encrypted_response["iv"])

cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
decryptor = cipher.decryptor()
padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

unpadder = padding.PKCS7(128).unpadder()
json_bytes = unpadder.update(padded_data) + unpadder.finalize()

# Get original response
original_data = json.loads(json_bytes.decode('utf-8'))
print(json.dumps(original_data, indent=2))
```

---

## 📚 Client Library (Python)

For easier integration, use this client library:

```python
import requests
import base64
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

class VibeSyncClient:
    """Client for VibeSync API with automatic decryption."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.key = b'VibeSync2025SecureKey1234567890X'
    
    def decrypt(self, encrypted_data, iv):
        """Decrypt response."""
        encrypted_bytes = base64.b64decode(encrypted_data)
        iv_bytes = base64.b64decode(iv)
        
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv_bytes),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        json_bytes = unpadder.update(padded_data) + unpadder.finalize()
        
        return json.loads(json_bytes.decode('utf-8'))
    
    def request(self, method, endpoint, **kwargs):
        """Make request and auto-decrypt response."""
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, **kwargs)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("encrypted"):
                return self.decrypt(data["data"], data["iv"])
        
        return response.json()
    
    def get(self, endpoint, **kwargs):
        return self.request("GET", endpoint, **kwargs)
    
    def post(self, endpoint, **kwargs):
        return self.request("POST", endpoint, **kwargs)
    
    def delete(self, endpoint, **kwargs):
        return self.request("DELETE", endpoint, **kwargs)

# Usage
client = VibeSyncClient()

# Create room
room = client.post("/rooms", json={"user_id": "user1", "username": "Alice"})
print(f"Room created: {room['room_code']}")

# Get room state
state = client.get(f"/rooms/{room['room_code']}")
print(f"Room state: {state}")

# Search songs
songs = client.get("/search/songs?query=arijit&limit=5")
print(f"Found {songs['total']} songs")
```

---

## 🔒 Security Notes

1. **Key Storage**: Never hardcode the encryption key in production. Use environment variables:
   ```bash
   export VIBESYNC_ENCRYPTION_KEY="your_secure_key_here"
   ```

2. **HTTPS**: Always use HTTPS in production to prevent man-in-the-middle attacks.

3. **Key Rotation**: Regularly rotate encryption keys for enhanced security.

4. **IV Uniqueness**: Each response uses a unique IV (initialization vector) for security.

---

## 🐛 Troubleshooting

### Issue: "Invalid padding"
- **Cause**: Incorrect key or IV
- **Solution**: Verify you're using the correct key: `VibeSync2025SecureKey1234567890`

### Issue: "Invalid base64"
- **Cause**: Data corruption during transmission
- **Solution**: Ensure proper JSON parsing and no data modification

### Issue: "JSON decode error"
- **Cause**: Decryption produced invalid data
- **Solution**: Check that the key matches exactly (case-sensitive)

---

## 📞 Support

If you encounter issues with decryption:
1. Verify the encryption key is exactly 32 bytes
2. Ensure IV is passed correctly from the response
3. Check that base64 decoding is working properly
4. Verify the cryptography library version

---

**Last Updated**: December 27, 2025  
**API Version**: 1.0.0
