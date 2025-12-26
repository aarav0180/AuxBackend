# VibeSync API - cURL Examples

Complete API reference with cURL commands for all endpoints.

**Base URL**: `http://localhost:8000`

---
## 🎵 Default Community Room

**VibeSync includes a permanent default room (`DEFAULT`) that:**
- ✅ Always available - created automatically on server start
- ✅ Cannot be deleted - protected from deletion
- ✅ Community room - anyone can join and add songs
- ✅ Continuous playback - music keeps playing as long as there are songs
- ✅ Perfect for public listening sessions

**Quick Start with Default Room**:
```bash
# Join the default room (no need to create)
curl -X POST "http://localhost:8000/rooms/DEFAULT/join?user_id=user1&username=Alice"

# Add a song to default room
curl -X POST "http://localhost:8000/rooms/DEFAULT/queue" \
  -H "Content-Type: application/json" \
  -d '{
    "jiosaavn_song_id": "song123",
    "user_id": "user1",
    "username": "Alice"
  }'

# Get stream from default room
curl -X GET "http://localhost:8000/rooms/DEFAULT/stream"
```

---
## 📋 Table of Contents

1. [Search Endpoints](#search-endpoints)
2. [Room Management](#room-management)
3. [Queue Operations](#queue-operations)
4. [Playback Control](#playback-control)
5. [Member Management](#member-management)
6. [Stream Info](#stream-info)

---

## 🔍 Search Endpoints

### 1. Search for Songs

Search JioSaavn for songs to add to queue.

```bash
curl -X GET "http://localhost:8000/search/songs?query=arijit%20singh&limit=10"
```

**Response**:
```json
{
  "success": true,
  "query": "arijit singh",
  "results": [
    {
      "id": "song123",
      "name": "Tum Hi Ho",
      "artists": "Arijit Singh",
      "album": "Aashiqui 2",
      "image_url": "https://...",
      "duration": 262,
      "download_url": "https://...",
      "download_urls": [
        {"quality": "128kbps", "url": "https://...", "bitrate": 128},
        {"quality": "320kbps", "url": "https://...", "bitrate": 320}
      ],
      "thumbnails": [
        {"url": "https://...", "quality": "150x150", "width": 150, "height": 150},
        {"url": "https://...", "quality": "500x500", "width": 500, "height": 500}
      ],
      "artists_simplified": [
        {"id": "artist1", "name": "Arijit Singh", "role": "primary", "image_url": "https://..."}
      ],
      "artists_detailed": [
        {
          "id": "artist1",
          "name": "Arijit Singh",
          "role": "primary",
          "image_url": "https://...",
          "bio": "...",
          "follower_count": 1000000,
          "is_verified": true
        }
      ]
    }
  ],
  "total": 10
}
```

---

### 2. Get Song Details

Get detailed information about a specific song.

```bash
curl -X GET "http://localhost:8000/search/songs/song123"
```

**Response**:
```json
{
  "id": "song123",
  "name": "Tum Hi Ho",
  "artists": "Arijit Singh",
  "album": "Aashiqui 2",
  "image_url": "https://...",
  "duration": 262,
  "download_url": "https://...",
  "download_urls": [...],
  "thumbnails": [...],
  "artists_simplified": [...],
  "artists_detailed": [...],
  "language": "Hindi",
  "year": "2013",
  "play_count": 5000000
}
```

---

### 3. Get Song Suggestions

Get similar song recommendations based on a song.

```bash
curl -X GET "http://localhost:8000/search/songs/song123/suggestions?limit=10"
```

**Response**:
```json
{
  "success": true,
  "suggestions": [
    {
      "id": "song456",
      "name": "Channa Mereya",
      "artists": "Arijit Singh",
      "album": "Ae Dil Hai Mushkil",
      "image_url": "https://...",
      "duration": 298,
      "download_url": "https://..."
    }
  ]
}
```

---

## 🏠 Room Management

### 4. Create a Room

Create a new listening room. Creator becomes the host.

```bash
curl -X POST "http://localhost:8000/rooms" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "username": "John Doe"
  }'
```

**Response**:
```json
{
  "success": true,
  "room_code": "ABC123",
  "message": "Room ABC123 created successfully"
}
```

---

### 5. Get Room State

Get current state of a room (queue, now playing, members).

```bash
curl -X GET "http://localhost:8000/rooms/ABC123"
```

**Response**:
```json
{
  "room_code": "ABC123",
  "host_user_id": "user123",
  "host_username": "John Doe",
  "created_at": "2025-12-26T10:30:00Z",
  "current_song": {
    "queue_id": "q1",
    "id": "song123",
    "name": "Tum Hi Ho",
    "artists": "Arijit Singh",
    "album": "Aashiqui 2",
    "image_url": "https://...",
    "duration": 262,
    "download_url": "https://...",
    "download_urls": [...],
    "thumbnails": [...],
    "artists_simplified": [...],
    "artists_detailed": [...],
    "added_by_user_id": "user123",
    "added_by_username": "John Doe",
    "added_at": "2025-12-26T10:31:00Z"
  },
  "song_start_time": "2025-12-26T10:31:30Z",
  "is_paused": false,
  "queue": [...],
  "queue_length": 5,
  "member_count": 3
}
```

---

### 6. Delete/Close Room

Close a room and disconnect all members. Host only.

**Note**: The default room (`DEFAULT`) cannot be deleted and will return a 403 error.

```bash
curl -X DELETE "http://localhost:8000/rooms/ABC123"
```

**Success Response**:
```json
{
  "success": true,
  "message": "Room ABC123 closed successfully"
}
```

**Error Response (Default Room)**:
```json
{
  "detail": "The default room cannot be deleted. It is a permanent community room."
}
```

---

## 🎵 Queue Operations

### 7. Add Song to Queue

Add a song to the room's queue by JioSaavn song ID.

**Moderation Rules**:
- ✅ Max 3 songs per user in queue
- ✅ Max 480 seconds (8 minutes) per song
- ✅ No duplicates in current queue (songs can be re-added after playing)

```bash
curl -X POST "http://localhost:8000/rooms/ABC123/queue" \
  -H "Content-Type: application/json" \
  -d '{
    "jiosaavn_song_id": "song456",
    "user_id": "user789",
    "username": "Jane Smith"
  }'
```

**Success Response**:
```json
{
  "success": true,
  "message": "'Channa Mereya' added to queue at position 2",
  "song": {
    "queue_id": "q2",
    "id": "song456",
    "name": "Channa Mereya",
    "artists": "Arijit Singh",
    "album": "Ae Dil Hai Mushkil",
    "image_url": "https://...",
    "duration": 298,
    "download_url": "https://...",
    "download_urls": [...],
    "thumbnails": [...],
    "artists_simplified": [...],
    "artists_detailed": [...],
    "added_by_user_id": "user789",
    "added_by_username": "Jane Smith",
    "added_at": "2025-12-26T10:35:00Z"
  },
  "queue_position": 2
}
```

**Error Responses**:

*User Quota Exceeded*:
```json
{
  "detail": "User quota exceeded. You can only have 3 songs pending in the queue at one time. Wait for your songs to play."
}
```

*Song Too Long*:
```json
{
  "detail": "Song too long (520s). Maximum allowed duration is 480 seconds (8 minutes)."
}
```

*Duplicate Song*:
```json
{
  "detail": "'Channa Mereya' is already in the queue"
}
```

---

### 8. Remove Song from Queue

Remove a song from the queue. Only the adder or host can remove.

```bash
curl -X DELETE "http://localhost:8000/rooms/ABC123/queue/q2?requesting_user_id=user789"
```

**Response**:
```json
{
  "success": true,
  "message": "'Channa Mereya' removed from queue",
  "data": {
    "removed_song": {
      "queue_id": "q2",
      "id": "song456",
      "name": "Channa Mereya",
      "artists": "Arijit Singh",
      "added_by_user_id": "user789",
      "added_by_username": "Jane Smith"
    }
  }
}
```

**Error Response** (Permission Denied):
```json
{
  "detail": "Only the song adder or room host can remove this song"
}
```

---

## ▶️ Playback Control

### 9. Get Sync State

Get current playback state for synchronization. **Poll this endpoint every 2-5 seconds**.

```bash
curl -X GET "http://localhost:8000/rooms/ABC123/sync"
```

**Response**:
```json
{
  "current_song": {
    "queue_id": "q1",
    "id": "song123",
    "name": "Tum Hi Ho",
    "artists": "Arijit Singh",
    "album": "Aashiqui 2",
    "image_url": "https://...",
    "duration": 262,
    "download_url": "https://...",
    "download_urls": [...],
    "thumbnails": [...],
    "artists_simplified": [...],
    "artists_detailed": [...],
    "added_by_user_id": "user123",
    "added_by_username": "John Doe",
    "added_at": "2025-12-26T10:31:00Z"
  },
  "server_time": "2025-12-26T10:33:45Z",
  "song_start_time": "2025-12-26T10:31:30Z",
  "is_paused": false,
  "seek_position_seconds": 135.5,
  "next_songs": [
    {
      "queue_id": "q2",
      "id": "song456",
      "name": "Channa Mereya",
      "artists": "Arijit Singh",
      "duration": 298,
      "download_url": "https://...",
      "download_urls": [...],
      "thumbnails": [...]
    },
    {
      "queue_id": "q3",
      "id": "song789",
      "name": "Ae Dil Hai Mushkil",
      "artists": "Arijit Singh",
      "duration": 274
    }
  ],
  "queue_length": 5
}
```

**Frontend Usage**:
```javascript
// Calculate seek position
const serverTime = new Date(response.server_time);
const songStartTime = new Date(response.song_start_time);
const seekPosition = (serverTime - songStartTime) / 1000; // seconds

// Or use the pre-calculated value
const seekPosition = response.seek_position_seconds;
```

---

### 10. Skip to Next Song

Skip current song and play next. **Host only**.

```bash
curl -X POST "http://localhost:8000/rooms/ABC123/skip?requesting_user_id=user123"
```

**Response**:
```json
{
  "success": true,
  "message": "Now playing: Channa Mereya",
  "data": {
    "current_song": {
      "queue_id": "q2",
      "id": "song456",
      "name": "Channa Mereya",
      "artists": "Arijit Singh",
      "duration": 298
    }
  }
}
```

---

### 11. Toggle Pause/Resume

Toggle playback pause state. **Host only**.

```bash
curl -X POST "http://localhost:8000/rooms/ABC123/pause?requesting_user_id=user123"
```

**Response (Paused)**:
```json
{
  "success": true,
  "message": "Paused",
  "data": {
    "is_paused": true
  }
}
```

**Response (Resumed)**:
```json
{
  "success": true,
  "message": "Playing",
  "data": {
    "is_paused": false
  }
}
```

---

### 12. Get Room Suggestions

Get song suggestions based on current/last played song in the room.

```bash
curl -X GET "http://localhost:8000/rooms/ABC123/suggestions?limit=10"
```

**Response**:
```json
{
  "success": true,
  "suggestions": [
    {
      "id": "song789",
      "name": "Ae Dil Hai Mushkil",
      "artists": "Arijit Singh",
      "album": "Ae Dil Hai Mushkil",
      "image_url": "https://...",
      "duration": 274,
      "download_url": "https://...",
      "download_urls": [...],
      "thumbnails": [...]
    }
  ]
}
```

---

## 👥 Member Management

### 13. Join a Room

Join an existing room and get full playback state.

```bash
curl -X POST "http://localhost:8000/rooms/ABC123/join?user_id=user999&username=Alice"
```

**Response**:
```json
{
  "success": true,
  "message": "Joined room ABC123",
  "data": {
    "room_code": "ABC123",
    "host_user_id": "user123",
    "host_username": "John Doe",
    "member_count": 4,
    "current_song": {
      "id": "song123",
      "name": "Tum Hi Ho",
      "artists": "Arijit Singh",
      "album": "Aashiqui 2",
      "duration": 262,
      "image_url": "https://...",
      "download_url": "https://...",
      "thumbnails": [
        {"url": "https://...", "quality": "50x50", "width": 50, "height": 50},
        {"url": "https://...", "quality": "150x150", "width": 150, "height": 150},
        {"url": "https://...", "quality": "500x500", "width": 500, "height": 500}
      ],
      "download_urls": [
        {"quality": "128kbps", "url": "https://...", "bitrate": 128},
        {"quality": "320kbps", "url": "https://...", "bitrate": 320},
        {"quality": "lossless", "url": "https://...", "bitrate": 960}
      ],
      "artists_simplified": [
        {"id": "artist1", "name": "Arijit Singh", "role": "primary", "image_url": "https://..."}
      ],
      "artists_detailed": [
        {
          "id": "artist1",
          "name": "Arijit Singh",
          "role": "primary",
          "image_url": "https://...",
          "bio": "Indian playback singer...",
          "follower_count": 10000000,
          "is_verified": true,
          "url": "https://..."
        }
      ],
      "added_by": "John Doe"
    },
    "all_stream_urls": [...],
    "stream_url": "https://...",
    "seek_position_seconds": 135.5,
    "is_paused": false,
    "server_time": "2025-12-26T10:33:45Z",
    "song_start_time": "2025-12-26T10:31:30Z",
    "next_songs": [
      {
        "queue_id": "q2",
        "id": "song456",
        "name": "Channa Mereya",
        "artists": "Arijit Singh",
        "duration": 298,
        "download_url": "https://...",
        "download_urls": [...],
        "thumbnails": [...]
      }
    ],
    "queue": [...],
    "queue_length": 5
  }
}
```

---

### 14. Leave a Room

Leave a room you've joined.

```bash
curl -X POST "http://localhost:8000/rooms/ABC123/leave?user_id=user999"
```

**Response**:
```json
{
  "success": true,
  "message": "Left room"
}
```

---

## 🎧 Stream Info

### 15. Get Stream Information

Get current audio stream URL and playback position with next songs for preloading.

```bash
curl -X GET "http://localhost:8000/rooms/ABC123/stream"
```

**Response (Song Playing)**:
```json
{
  "success": true,
  "message": "Stream ready",
  "data": {
    "stream_url": "https://aac.saavncdn.com/...",
    "all_stream_urls": [
      {"quality": "128kbps", "url": "https://...", "bitrate": 128},
      {"quality": "320kbps", "url": "https://...", "bitrate": 320},
      {"quality": "lossless", "url": "https://...", "bitrate": 960}
    ],
    "current_song": {
      "id": "song123",
      "name": "Tum Hi Ho",
      "artists": "Arijit Singh",
      "album": "Aashiqui 2",
      "image_url": "https://...",
      "thumbnails": [
        {"url": "https://...", "quality": "50x50", "width": 50, "height": 50},
        {"url": "https://...", "quality": "150x150", "width": 150, "height": 150},
        {"url": "https://...", "quality": "500x500", "width": 500, "height": 500}
      ],
      "artists_simplified": [
        {"id": "artist1", "name": "Arijit Singh", "role": "primary", "image_url": "https://..."}
      ],
      "artists_detailed": [
        {
          "id": "artist1",
          "name": "Arijit Singh",
          "role": "primary",
          "image_url": "https://...",
          "bio": "Indian playback singer...",
          "follower_count": 10000000,
          "is_verified": true,
          "url": "https://..."
        }
      ],
      "duration": 262,
      "added_by": "John Doe"
    },
    "seek_position_seconds": 135.5,
    "is_paused": false,
    "server_time": "2025-12-26T10:33:45Z",
    "next_songs": [
      {
        "queue_id": "q2",
        "id": "song456",
        "name": "Channa Mereya",
        "artists": "Arijit Singh",
        "duration": 298,
        "download_url": "https://...",
        "download_urls": [
          {"quality": "128kbps", "url": "https://...", "bitrate": 128},
          {"quality": "320kbps", "url": "https://...", "bitrate": 320}
        ],
        "thumbnails": [...]
      },
      {
        "queue_id": "q3",
        "id": "song789",
        "name": "Ae Dil Hai Mushkil",
        "duration": 274
      }
    ],
    "queue_length": 5
  }
}
```

**Response (No Song Playing)**:
```json
{
  "success": true,
  "message": "No song currently playing",
  "data": {
    "stream_url": null,
    "current_song": null,
    "seek_position_seconds": 0,
    "is_paused": false,
    "next_songs": [],
    "queue_length": 0
  }
}
```

---

## 🎯 Complete Workflow Example

Here's a complete flow from creating a room to streaming music:

```bash
# Option 1: Use the Default Community Room (Easiest!)
# =====================================================

# 1. Search for songs
curl -X GET "http://localhost:8000/search/songs?query=arijit%20singh&limit=5"

# 2. Add song to default room (no need to create room!)
curl -X POST "http://localhost:8000/rooms/DEFAULT/queue" \
  -H "Content-Type: application/json" \
  -d '{
    "jiosaavn_song_id": "song123",
    "user_id": "user1",
    "username": "Alice"
  }'

# 3. Join the default room
curl -X POST "http://localhost:8000/rooms/DEFAULT/join?user_id=user1&username=Alice"

# 4. Start streaming from default room
curl -X GET "http://localhost:8000/rooms/DEFAULT/stream"


# Option 2: Create Your Own Private Room
# ========================================

# 1. Create a room
curl -X POST "http://localhost:8000/rooms" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "host1", "username": "DJ Mike"}'
# Response: {"room_code": "ABC123"}

# 2. Search for songs
curl -X GET "http://localhost:8000/search/songs?query=arijit%20singh&limit=5"
# Response: {"results": [{"id": "song123", "name": "Tum Hi Ho", ...}]}

# 3. Add song to queue
curl -X POST "http://localhost:8000/rooms/ABC123/queue" \
  -H "Content-Type: application/json" \
  -d '{
    "jiosaavn_song_id": "song123",
    "user_id": "host1",
    "username": "DJ Mike"
  }'
# Response: {"success": true, "queue_position": 1}

# 4. Join the room (as listener)
curl -X POST "http://localhost:8000/rooms/ABC123/join?user_id=listener1&username=Alice"
# Response: Full playback state with stream_url and seek_position

# 5. Get stream info
curl -X GET "http://localhost:8000/rooms/ABC123/stream"
# Response: stream_url, quality options, thumbnails, next songs

# 6. Poll sync state (every 2-5 seconds)
curl -X GET "http://localhost:8000/rooms/ABC123/sync"
# Response: Current playback position and state

# 7. Skip song (host only)
curl -X POST "http://localhost:8000/rooms/ABC123/skip?requesting_user_id=host1"
# Response: Now playing next song

# 8. Toggle pause (host only)
curl -X POST "http://localhost:8000/rooms/ABC123/pause?requesting_user_id=host1"
# Response: {"is_paused": true}

# 9. Leave room
curl -X POST "http://localhost:8000/rooms/ABC123/leave?user_id=listener1"
# Response: {"success": true}
```

---

## 🛡️ Moderation Features

The API includes built-in moderation to prevent spam and abuse:

### User Quota System
- Each user can have **max 3 songs** pending in the queue
- Count automatically decrements when songs play or are removed
- Prevents queue flooding by single users

### Duration Limits
- Songs longer than **8 minutes (480 seconds)** are rejected
- Ensures reasonable queue progression

### Anti-Repetitiveness
- **Duplicate Detection**: Songs already in queue are rejected
- **Re-queue Allowed**: Songs can be added again after they finish playing
- **Fuzzy Matching**: Compares by ID + normalized name/artist

### Secure Deletion
- Only the song adder or room host can remove songs
- Prevents malicious removals by other users

---

## 📊 Response Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created (room, song added)
- `400 Bad Request` - Validation error, quota exceeded, duplicate, etc.
- `403 Forbidden` - Permission denied (not host, wrong user)
- `404 Not Found` - Room or song not found
- `502 Bad Gateway` - External API (JioSaavn) error

---

## 🚀 Tips for Frontend Integration

1. **Polling**: Call `/sync` every 2-5 seconds for real-time updates
2. **Preloading**: Use `next_songs` array to preload upcoming tracks
3. **Quality Selection**: Let users choose from `all_stream_urls` based on bandwidth
4. **Thumbnails**: Use appropriate thumbnail size for different UI elements (50x50 for lists, 500x500 for now playing)
5. **Error Handling**: Show user-friendly messages for moderation errors
6. **Artist Info**: Display simplified info in lists, detailed info in artist pages

---

## 📝 Notes

- All timestamps are in ISO 8601 format (UTC)
- Room codes are 6-character alphanumeric strings (except `DEFAULT`)
- **Default Room**: `DEFAULT` is always available and cannot be deleted
- Song IDs are JioSaavn song identifiers
- User IDs should be unique per user (generated by your auth system)
- The API is stateless except for in-memory room state
- State is lost on server restart, but the default room is automatically recreated

---

## 🏆 Default Room Benefits

The `DEFAULT` room provides:

1. **No Setup Required**: Jump straight into listening without creating a room
2. **Community Experience**: Public room where everyone can contribute
3. **Always Available**: Persists across sessions (recreated on restart)
4. **Perfect for Testing**: Quick way to test the API and features
5. **24/7 Music**: As long as users keep adding songs, music keeps playing

**Use Cases**:
- Public listening parties
- Collaborative playlists
- Testing and development
- Community radio experience
- Quick music sharing

---

**Generated**: December 26, 2025  
**API Version**: 1.0.0
