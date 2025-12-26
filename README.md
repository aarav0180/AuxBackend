# VibeSync Backend 🎵

A production-grade collaborative music streaming backend built with FastAPI that enables synchronized listening experiences with enterprise-level security, intelligent moderation, and comprehensive music metadata.

## 🌟 Features

### Core Functionality
- **Room Management**: Create and manage listening rooms with unique codes
- **Queue System**: Advanced queue management with intelligent ordering
- **Synchronized Playback**: Millisecond-accurate playback synchronization across all clients
- **JioSaavn Integration**: Search and stream millions of high-quality songs
- **Real-time Sync**: Sub-second accuracy for perfect group listening

### 🎵 Enhanced Music Data
- **Multi-Quality Streaming**: Access to all available quality URLs (12kbps to 320kbps)
- **Complete Thumbnails**: All thumbnail sizes (50x50 to 500x500) for rich UI experiences
- **Artist Information**: Detailed artist metadata including:
  - Simplified artist data (name, role, type, image)
  - Detailed artist info (biography, followers, verified status, social links)
- **Next Songs Preview**: Get next 3-5 songs in queue for seamless UI updates
- **Comprehensive Metadata**: Duration, year, language, album art, copyright info, and more

### 🛡️ Security & Encryption
- **AES-256-CBC Encryption**: All API responses encrypted end-to-end
- **Automatic Middleware**: Transparent encryption without code changes
- **Secure Key Management**: Environment-based key configuration
- **Documentation Exemption**: `/docs`, `/redoc`, and `/openapi.json` remain accessible
- **Content-Length Optimization**: Automatic header management for encrypted payloads

### 🎯 Intelligent Moderation
- **User Quotas**: Maximum 3 songs per user in queue (configurable)
- **Duration Limits**: Songs capped at 8 minutes (480 seconds)
- **Anti-Repetitiveness**: Fuzzy matching prevents duplicate songs in queue
- **Secure Deletion**: Only song adder or room host can remove songs
- **Rate Limiting Ready**: Built-in quota tracking for future rate limiting

### 🏠 Default Community Room
- **Always Available**: "DEFAULT" room auto-created on startup
- **Protected**: Cannot be deleted or closed
- **Public Access**: Perfect for community listening parties
- **Configurable**: Customize via environment variables

## 🚀 Tech Stack

- **Python 3.11+** - Modern async/await support
- **FastAPI 0.109.0** - High-performance async web framework with automatic OpenAPI
- **Pydantic v2** - Advanced data validation and settings management
- **httpx 0.26.0** - Async HTTP client for external API calls
- **Cryptography 41.0.7** - Industry-standard encryption library
- **Uvicorn 0.27.0** - Lightning-fast ASGI server

## 📦 Quick Start

### 1. Clone & Install

```bash
git clone <repository-url>
cd streamBackend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

**Edit `.env` with your settings:**

```env
# Application Configuration
APP_NAME=VibeSync
ENVIRONMENT=development

# Server Configuration
HOST=0.0.0.0
PORT=8000

# JioSaavn API
JIOSAAVN_API_BASE_URL=https://jiosavan-api-with-playlist.vercel.app

# Room Configuration
MAX_QUEUE_SIZE=50
SYNC_TOLERANCE_SECONDS=2.0

# Default Community Room
DEFAULT_ROOM_CODE=DEFAULT
DEFAULT_ROOM_HOST_ID=system
DEFAULT_ROOM_HOST_NAME=VibeSync Community

# Moderation Settings
MAX_SONGS_PER_USER=3
MAX_SONG_DURATION_SECONDS=480

# Security (IMPORTANT: Change in production!)
ENCRYPTION_KEY=VibeSync2025SecureKey1234567890X
```

### 3. Run the Server

```bash
# Development with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Access the API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📡 API Endpoints

### Room Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/rooms` | Create a new room | ❌ |
| GET | `/rooms/{room_code}` | Get room state | ❌ |
| DELETE | `/rooms/{room_code}` | Close a room (host only) | ✅ |

### Queue Operations

| Method | Endpoint | Description | Moderation |
|--------|----------|-------------|------------|
| POST | `/rooms/{room_code}/queue` | Add song to queue | ✅ Quota, Duration, Duplicates |
| DELETE | `/rooms/{room_code}/queue/{queue_id}` | Remove song from queue | ✅ Adder or Host only |

### Playback & Sync

| Method | Endpoint | Description | Returns |
|--------|----------|-------------|---------|
| GET | `/rooms/{room_code}/sync` | Get sync state for clients | Current song + next 3-5 songs |
| POST | `/rooms/{room_code}/skip` | Skip current song | Host only |
| POST | `/rooms/{room_code}/pause` | Toggle pause | Host only |

### Search

| Method | Endpoint | Description | Features |
|--------|----------|-------------|----------|
| GET | `/search/songs` | Search for songs | All qualities + thumbnails + artists |
| GET | `/search/songs/{song_id}` | Get song details | Complete metadata |
| GET | `/search/songs/{song_id}/suggestions` | Get song suggestions | Related tracks |

## 🔐 Encryption & Decryption

All API responses (except documentation endpoints) are encrypted with AES-256-CBC. See [decryption.md](decryption.md) for implementation examples in:
- Python
- JavaScript/TypeScript
- Java
- Go
- Ruby

### Response Format

```json
{
  "encrypted_data": "base64_encrypted_payload",
  "iv": "base64_initialization_vector"
}
```

### Decryption Example (Python)

```python
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

def decrypt_response(encrypted_data: str, iv: str, key: str) -> dict:
    cipher = Cipher(
        algorithms.AES(key.encode('utf-8')),
        modes.CBC(base64.b64decode(iv)),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    
    decrypted_padded = decryptor.update(base64.b64decode(encrypted_data))
    decrypted_padded += decryptor.finalize()
    
    unpadder = padding.PKCS7(128).unpadder()
    decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
    
    return json.loads(decrypted.decode('utf-8'))
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI App                          │
│                     (main.py + ASGI)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   Middleware      │
                    │ - CORS            │
                    │ - Encryption      │
                    │ - Exception       │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌───────▼────────┐
│  Room Routes   │   │  Search Routes  │   │  Health Route  │
│  (api/rooms)   │   │  (api/search)   │   │                │
└───────┬────────┘   └────────┬────────┘   └────────────────┘
        │                     │
        │            ┌────────▼────────┐
        │            │  JioSaavn       │
        │            │  Service        │
        │            │ (External API)  │
        │            └─────────────────┘
        │
┌───────▼────────┐
│  Room Manager  │
│  Service       │
│ - Queue Mgmt   │
│ - Moderation   │
│ - Sync Logic   │
└────────────────┘
```

### Data Flow

1. **Client Request** → Encrypted/Plain HTTP
2. **Middleware Layer** → CORS, Exception Handling
3. **Route Handler** → Validation via Pydantic
4. **Service Layer** → Business logic, external API calls
5. **Response** → Pydantic model → JSON → Encryption
6. **Client** → Decrypt → Use data

## 🎯 Synchronization Logic

### How It Works

1. **Host creates a room** → Gets unique 6-character room code
2. **Listeners join** with room code
3. **Songs added to queue** → Validated by moderation system
4. **Playback starts** → `song_start_time` recorded
5. **Clients poll** `/sync` endpoint every 1-2 seconds
6. **Frontend calculates**:
   ```javascript
   const elapsedTime = serverTime - songStartTime;
   audioPlayer.currentTime = elapsedTime;
   ```

### Sync Response Example

```json
{
  "current_song": {
    "id": "abc123",
    "name": "Shape of You",
    "artists": "Ed Sheeran",
    "duration": 234,
    "download_urls": [
      {
        "quality": "320kbps",
        "url": "https://...",
        "bitrate": 320
      }
    ],
    "thumbnails": [
      {
        "quality": "500x500",
        "url": "https://..."
      }
    ],
    "artists_simplified": [
      {
        "name": "Ed Sheeran",
        "role": "primary_artists",
        "image_url": "https://..."
      }
    ]
  },
  "server_time": "2025-01-15T12:00:00Z",
  "song_start_time": "2025-01-15T11:56:26Z",
  "is_paused": false,
  "seek_position_seconds": 214.5,
  "next_songs": [
    {
      "id": "xyz456",
      "name": "Perfect",
      "artists": "Ed Sheeran",
      "duration": 263
    }
  ]
}
```

## 🛡️ Moderation System

### User Quotas

Each user can have maximum **3 songs** in the queue at once:

```python
# Automatically tracked per user_id
user_pending_counts = {
    "user123": 2,  # Can add 1 more
    "user456": 3   # Quota reached
}
```

### Duration Limits

Songs longer than **8 minutes** (480 seconds) are rejected:

```json
{
  "success": false,
  "error": "Song duration exceeds maximum allowed duration of 480 seconds"
}
```

### Anti-Repetitiveness

Fuzzy matching prevents similar songs:

- Checks title similarity (Levenshtein distance)
- Checks artist overlap
- Prevents exact duplicates in current queue

```python
def _is_song_similar(song1, song2) -> bool:
    title_similarity = similar(song1.name, song2.name)
    artists1 = set(song1.artists.lower().split(','))
    artists2 = set(song2.artists.lower().split(','))
    artist_overlap = len(artists1 & artists2) / max(len(artists1), len(artists2))
    
    return title_similarity > 0.85 and artist_overlap > 0.5
```

### Secure Deletion

Only the user who added the song or the room host can remove it:

```python
if queue_item.added_by_user_id not in [user_id, room.host_id]:
    raise PermissionDeniedError("Only song adder or host can remove")
```

## 📂 Project Structure

```
streamBackend/
├── main.py                      # Application entry point + middleware
├── requirements.txt             # Python dependencies
├── .env                        # Environment variables (gitignored)
├── .env.example                # Environment template
├── README.md                   # This file
├── curls.md                    # API usage examples with curl
├── decryption.md               # Decryption guide (multi-language)
└── src/
    ├── __init__.py
    ├── api/                    # API route handlers
    │   ├── __init__.py
    │   ├── rooms.py           # Room & queue endpoints
    │   └── search.py          # Search endpoints
    ├── core/                   # Core configuration
    │   ├── __init__.py
    │   ├── config.py          # Settings (env-based)
    │   ├── encryption.py      # AES-256 encryption
    │   └── exceptions.py      # Custom exceptions
    ├── models/                 # Pydantic models
    │   ├── __init__.py
    │   └── schemas.py         # Request/Response schemas
    └── services/               # Business logic
        ├── __init__.py
        ├── jiosaavn_service.py  # JioSaavn API integration
        └── room_manager.py      # Room state & moderation
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | VibeSync | Application name |
| `ENVIRONMENT` | development | Environment (dev/staging/prod) |
| `HOST` | 0.0.0.0 | Server bind address |
| `PORT` | 8000 | Server port |
| `JIOSAAVN_API_BASE_URL` | Required | JioSaavn API endpoint |
| `MAX_QUEUE_SIZE` | 50 | Maximum songs in queue |
| `SYNC_TOLERANCE_SECONDS` | 2.0 | Sync accuracy threshold |
| `DEFAULT_ROOM_CODE` | DEFAULT | Default community room code |
| `DEFAULT_ROOM_HOST_ID` | system | Default room host ID |
| `DEFAULT_ROOM_HOST_NAME` | VibeSync Community | Default room host name |
| `MAX_SONGS_PER_USER` | 3 | User quota limit |
| `MAX_SONG_DURATION_SECONDS` | 480 | Max song duration (8 min) |
| `ENCRYPTION_KEY` | **REQUIRED** | 32-byte AES-256 key |

### Security Notes

⚠️ **IMPORTANT**: Change `ENCRYPTION_KEY` in production!

```bash
# Generate a secure 32-byte key
python -c "import secrets; print(secrets.token_urlsafe(32)[:32])"
```

## 📚 API Documentation

Comprehensive API examples available in [curls.md](curls.md):

- Creating rooms
- Adding songs with validation
- Removing songs (secure)
- Searching with full metadata
- Getting sync state with next songs
- Handling encrypted responses
- Error scenarios

## 🚀 Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ENVIRONMENT=production
ENV HOST=0.0.0.0
ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```bash
docker build -t vibesync-backend .
docker run -p 8000:8000 --env-file .env vibesync-backend
```

### Production Checklist

- [ ] Generate secure `ENCRYPTION_KEY` (32 bytes)
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure proper `JIOSAAVN_API_BASE_URL`
- [ ] Use process manager (systemd, PM2, or Docker)
- [ ] Set up reverse proxy (Nginx, Caddy)
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS for your frontend domain
- [ ] Set up logging and monitoring
- [ ] Configure rate limiting (nginx/middleware)
- [ ] Regular security audits

### Systemd Service

```ini
[Unit]
Description=VibeSync Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/vibesync
EnvironmentFile=/opt/vibesync/.env
ExecStart=/usr/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🐛 Troubleshooting

### Common Issues

**1. Encryption Key Length Error**
```
Error: AES key must be 32 bytes
```
**Solution**: Ensure `ENCRYPTION_KEY` is exactly 32 characters.

**2. Content-Length Mismatch**
```
Response content longer than Content-Length
```
**Solution**: Already fixed in middleware - ensure you're on latest version.

**3. User Quota Exceeded**
```json
{"success": false, "error": "User has reached maximum of 3 songs in queue"}
```
**Solution**: User must wait for their songs to finish playing or be removed.

**4. Song Too Long**
```json
{"success": false, "error": "Song duration exceeds maximum allowed"}
```
**Solution**: Choose songs under 8 minutes or adjust `MAX_SONG_DURATION_SECONDS`.

**5. Duplicate Song**
```json
{"success": false, "error": "A similar song is already in the queue"}
```
**Solution**: Queue already contains this song - wait for it to finish.

### Debug Mode

```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
python main.py
```

## 🗺️ Roadmap

### Version 2.0 (In Progress)
- [ ] PostgreSQL persistence
- [ ] Redis caching for room state
- [ ] WebSocket support for real-time updates
- [ ] User authentication with JWT
- [ ] Room privacy settings (public/private/password)
- [ ] Vote-to-skip functionality
- [ ] Playlist support
- [ ] Song history and analytics

### Version 3.0 (Planned)
- [ ] Multi-service support (Spotify, YouTube Music)
- [ ] AI-powered song recommendations
- [ ] Advanced moderation (profanity filter, content rating)
- [ ] User profiles and preferences
- [ ] Room analytics dashboard
- [ ] Mobile app integration
- [ ] Chat functionality

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public functions
- Add tests for new features

## 📄 License

MIT License - see LICENSE file for details

## 📞 Support

- **Documentation**: See `/docs` endpoint
- **Issues**: GitHub Issues
- **Email**: support@vibesync.example

---

**Built with ❤️ using FastAPI** | **Powered by JioSaavn API** | **Secured with AES-256**
