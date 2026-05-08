# 🔍 COMPREHENSIVE SEARCH APIS - Camera Tracking AI

**Last Updated**: May 6, 2026  
**Status**: ✅ COMPLETE - All search endpoints implemented

---

## 📋 API ENDPOINTS OVERVIEW

### Person Search APIs
- `POST /api/persons/search/advanced` - Advanced multi-criteria search
- `POST /api/persons/search/by-appearance` - Search by clothing colors
- `POST /api/persons/search/by-location-time` - Search by location and time

### Vehicle Search APIs
- `POST /api/vehicles/search/advanced` - Advanced multi-criteria search
- `GET /api/vehicles/search/by-license-plate` - Search by license plate
- `POST /api/vehicles/search/by-type-color` - Search by vehicle type and color

### Alert Search APIs
- `POST /api/alerts/search/advanced` - Advanced alert search
- `GET /api/alerts/search/by-type-severity` - Search by type and severity
- `GET /api/alerts/search/active` - Get all active alerts

### Face Search APIs
- `POST /api/faces/search/embedding` - Search by face embedding
- `GET /api/faces/search/by-person-id` - Get person's face history
- `GET /api/faces/search/with-embedding` - Find persons with embeddings

---

## 👤 PERSON SEARCH ENDPOINTS

### 1. Advanced Person Search

**Endpoint**: `POST /api/persons/search/advanced`

**Description**: Search persons by multiple attributes (appearance, location, time, confidence)

**Request Body**:
```json
{
  "location": "cam_01",
  "start_time": "2026-05-06T08:00:00Z",
  "end_time": "2026-05-06T18:00:00Z",
  "shirt_color": "blue",
  "pants_color": "black",
  "hair_color": "black",
  "confidence_min": 0.8,
  "confidence_max": 1.0,
  "page": 1,
  "limit": 50
}
```

**Response**:
```json
{
  "status": "success",
  "total_results": 5,
  "current_page": 1,
  "results_per_page": 50,
  "total_pages": 1,
  "results": [
    {
      "person_id": "person_123",
      "location": "cam_01",
      "timestamp": "2026-05-06T10:30:45Z",
      "shirt_colors": [
        {"rank": 1, "name": "Xanh dương", "rgb": [0, 0, 255]},
        {"rank": 2, "name": "Trắng", "rgb": [255, 255, 255]}
      ],
      "pants_colors": [{"rank": 1, "name": "Đen", "rgb": [0, 0, 0]}],
      "hair_colors": [{"rank": 1, "name": "Đen", "rgb": [0, 0, 0]}],
      "confidence": 0.92
    }
  ]
}
```

**Query Filters** (all optional):
- `location` - Camera location (substring match)
- `start_time` - Start time (ISO 8601 format)
- `end_time` - End time (ISO 8601 format)
- `shirt_color` - Shirt color name
- `pants_color` - Pants color name
- `hair_color` - Hair color name
- `confidence_min` - Minimum confidence (0.0-1.0)
- `confidence_max` - Maximum confidence (0.0-1.0)
- `page` - Page number (default 1)
- `limit` - Results per page (max 500, default 50)

---

### 2. Search by Appearance

**Endpoint**: `POST /api/persons/search/by-appearance`

**Description**: Quick search by clothing and hair colors to find similar-looking individuals

**Request Body**:
```json
{
  "hair_color": "black",
  "shirt_color": "blue",
  "pants_color": "black",
  "confidence_min": 0.75,
  "limit": 20
}
```

**Response**:
```json
{
  "status": "success",
  "query_filters": {
    "hair_color": "black",
    "shirt_color": "blue",
    "pants_color": "black",
    "confidence_min": 0.75
  },
  "results_count": 3,
  "results": [
    { "person_id": "...", "..." }
  ]
}
```

**Use Cases**:
- Finding suspects based on witness description
- Tracking person with specific outfit
- Comparing multiple sightings of same person

---

### 3. Search by Location & Time

**Endpoint**: `POST /api/persons/search/by-location-time`

**Description**: Find all people detected at specific location during time period

**Request Body**:
```json
{
  "location": "cam_01",
  "start_time": "2026-05-06T08:00:00Z",
  "end_time": "2026-05-06T18:00:00Z",
  "limit": 100
}
```

**Response**:
```json
{
  "status": "success",
  "location": "cam_01",
  "time_range": {
    "start": "2026-05-06T08:00:00Z",
    "end": "2026-05-06T18:00:00Z"
  },
  "results_count": 42,
  "results": [...]
}
```

**Use Cases**:
- Timeline analysis of specific location
- Occupancy reports
- Access control audit

---

## 🚗 VEHICLE SEARCH ENDPOINTS

### 1. Advanced Vehicle Search

**Endpoint**: `POST /api/vehicles/search/advanced`

**Description**: Search vehicles by type, plate, color, location, and time

**Request Body**:
```json
{
  "vehicle_type": "car",
  "license_plate": "51A-12345",
  "vehicle_color": "white",
  "location": "cam_01",
  "start_time": "2026-05-06T08:00:00Z",
  "end_time": "2026-05-06T18:00:00Z",
  "confidence_min": 0.8,
  "page": 1,
  "limit": 50
}
```

**Response**:
```json
{
  "status": "success",
  "total_results": 2,
  "current_page": 1,
  "results_per_page": 50,
  "total_pages": 1,
  "results": [
    {
      "vehicle_id": "vehicle_456",
      "vehicle_type": "car",
      "license_plate": "51A-12345",
      "vehicle_colors": [
        {"rank": 1, "name": "Trắng", "rgb": [255, 255, 255]},
        {"rank": 2, "name": "Bạc", "rgb": [192, 192, 192]}
      ],
      "location": "cam_01",
      "timestamp": "2026-05-06T10:15:30Z",
      "confidence": 0.94
    }
  ]
}
```

---

### 2. Search by License Plate

**Endpoint**: `GET /api/vehicles/search/by-license-plate?license_plate=51A-12345&limit=50`

**Description**: Find all sightings of a specific vehicle by plate number

**Query Parameters**:
- `license_plate` - License plate number (required, substring match)
- `limit` - Max results (optional, default 50)

**Response**:
```json
{
  "status": "success",
  "license_plate": "51A-12345",
  "results_count": 5,
  "results": [...]
}
```

**Use Cases**:
- Tracking stolen vehicles
- Fleet management
- Law enforcement investigations

---

### 3. Search by Type & Color

**Endpoint**: `POST /api/vehicles/search/by-type-color`

**Description**: Find vehicles matching type and color combination

**Request Body**:
```json
{
  "vehicle_type": "car",
  "vehicle_color": "white",
  "location": "cam_01",
  "limit": 30
}
```

**Response**:
```json
{
  "status": "success",
  "filters": {
    "vehicle_type": "car",
    "vehicle_color": "white",
    "location": "cam_01"
  },
  "results_count": 12,
  "results": [...]
}
```

---

## 🚨 ALERT SEARCH ENDPOINTS

### 1. Advanced Alert Search

**Endpoint**: `POST /api/alerts/search/advanced`

**Description**: Search alerts by type, status, severity, and location

**Request Body**:
```json
{
  "alert_type": "fire",
  "status": "active",
  "severity": "high",
  "location": "cam_01",
  "start_time": "2026-05-06T08:00:00Z",
  "end_time": "2026-05-06T18:00:00Z",
  "page": 1,
  "limit": 50
}
```

**Response**:
```json
{
  "status": "success",
  "total_results": 3,
  "current_page": 1,
  "results_per_page": 50,
  "total_pages": 1,
  "results": [
    {
      "id": 1,
      "alert_type": "fire",
      "severity": "high",
      "status": "active",
      "location": "cam_01",
      "timestamp": "2026-05-06T14:30:00Z",
      "description": "Fire detected in warehouse"
    }
  ]
}
```

**Alert Types**:
- `fire` - Fire/smoke detection
- `suspicious` - Suspicious activity
- `missing_person` - Missing person alert
- `vehicle_stolen` - Stolen vehicle

**Status Values**:
- `active` - Unresolved alert
- `escalated` - High priority
- `resolved` - Closed
- `false_alarm` - False alarm

**Severity Levels**:
- `low` - Low priority
- `normal` - Standard priority
- `high` - High priority
- `critical` - Critical/immediate action needed

---

### 2. Search by Type & Severity

**Endpoint**: `GET /api/alerts/search/by-type-severity?alert_type=fire&severity=high&limit=50`

**Description**: Quick search for specific alert types with severity level

**Query Parameters**:
- `alert_type` - Alert type (optional)
- `severity` - Severity level (optional)
- `limit` - Max results (optional, default 50)

**Response**:
```json
{
  "status": "success",
  "filters": {
    "alert_type": "fire",
    "severity": "high"
  },
  "results_count": 3,
  "results": [...]
}
```

---

### 3. Get Active Alerts

**Endpoint**: `GET /api/alerts/search/active?severity=critical&location=cam_01&limit=100`

**Description**: Get all currently active (unresolved) alerts for incident dashboard

**Query Parameters**:
- `severity` - Filter by severity (optional)
- `location` - Filter by location (optional)
- `limit` - Max results (optional, default 100)

**Response**:
```json
{
  "status": "success",
  "active_alerts_count": 5,
  "critical_alerts": 2,
  "high_alerts": 1,
  "results": [...]
}
```

**Use Cases**:
- Real-time incident dashboard
- Alert prioritization
- Emergency response coordination

---

## 👁️ FACE SEARCH ENDPOINTS

### 1. Search by Embedding

**Endpoint**: `POST /api/faces/search/embedding`

**Description**: Find similar faces using face embedding (512-dimensional vector)

**Request Body**:
```json
{
  "embedding": [0.123, 0.456, -0.789, ..., 0.234],  // 512 values
  "threshold": 0.6,
  "limit": 20
}
```

**Response**:
```json
{
  "status": "success",
  "query_threshold": 0.6,
  "matches_count": 3,
  "results": [
    {
      "person_id": "person_123",
      "similarity": 0.87,
      "similarity_percent": 87.0,
      "location": "cam_01",
      "timestamp": "2026-05-06T10:30:45Z",
      "confidence": 0.92
    }
  ]
}
```

**Parameters**:
- `embedding` - 512-dimensional face embedding vector (required)
- `threshold` - Similarity threshold 0.0-1.0 (default 0.6)
- `limit` - Max results (default 20, max 100)

**Use Cases**:
- Face-based person search
- Finding repeat visitors
- Security screening

---

### 2. Search by Person ID

**Endpoint**: `GET /api/faces/search/by-person-id?person_id=person_123&start_time=...&limit=50`

**Description**: Get complete detection history for a specific person

**Query Parameters**:
- `person_id` - Person ID (required)
- `start_time` - From this time (optional, ISO 8601)
- `end_time` - Until this time (optional, ISO 8601)
- `limit` - Max results (optional, default 50)

**Response**:
```json
{
  "status": "success",
  "person_id": "person_123",
  "detections_count": 12,
  "locations": ["cam_01", "cam_02", "cam_05"],
  "results": [...]
}
```

---

### 3. Search Persons with Embeddings

**Endpoint**: `GET /api/faces/search/with-embedding?location=cam_01&page=1&limit=20`

**Description**: Find all persons that have registered face embeddings (FaceID database)

**Query Parameters**:
- `location` - Filter by location (optional)
- `start_time` - From this time (optional)
- `end_time` - Until this time (optional)
- `page` - Page number (default 1)
- `limit` - Results per page (default 20, max 200)

**Response**:
```json
{
  "status": "success",
  "total_with_embeddings": 156,
  "current_page": 1,
  "results_per_page": 20,
  "total_pages": 8,
  "results": [...]
}
```

---

## 📊 USAGE EXAMPLES

### Example 1: Find a suspect matching description

```bash
curl -X POST http://localhost:5000/api/persons/search/by-appearance \
  -H "Content-Type: application/json" \
  -d '{
    "hair_color": "black",
    "shirt_color": "blue",
    "pants_color": "black",
    "confidence_min": 0.75
  }'
```

### Example 2: Track a stolen vehicle

```bash
curl -X GET "http://localhost:5000/api/vehicles/search/by-license-plate?license_plate=51A-12345&limit=100"
```

### Example 3: Get all high-priority alerts

```bash
curl -X GET "http://localhost:5000/api/alerts/search/active?severity=high"
```

### Example 4: Find face matches

```bash
curl -X POST http://localhost:5000/api/faces/search/embedding \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [...512 float values...],
    "threshold": 0.6,
    "limit": 10
  }'
```

### Example 5: Advanced search for location audit

```bash
curl -X POST http://localhost:5000/api/persons/search/advanced \
  -H "Content-Type: application/json" \
  -d '{
    "location": "cam_01",
    "start_time": "2026-05-06T08:00:00Z",
    "end_time": "2026-05-06T18:00:00Z",
    "confidence_min": 0.8,
    "page": 1,
    "limit": 100
  }'
```

---

## 🔄 Response Format

All search endpoints return responses in this standard format:

```json
{
  "status": "success" | "error",
  "total_results": number,
  "results_count": number,
  "current_page": number,
  "total_pages": number,
  "results": [
    {
      // Individual record object
    }
  ]
}
```

---

## ⚙️ Performance Notes

| Query | Expected Time | Database Size |
|-------|---|---|
| By appearance | 50-200ms | 10k persons |
| By location-time | 100-500ms | 100k persons |
| By license plate | 30-100ms | 10k vehicles |
| By embedding | 200-800ms | 1k known faces |
| Advanced search | 100-500ms | 10k+ records |

**Optimization Tips**:
1. Use specific filters to reduce result set
2. Limit results to necessary amount
3. Use time ranges to narrow scope
4. Increase threshold for face similarity (fewer matches)
5. Use pagination for large result sets

---

## 📝 IMPLEMENTATION STATUS

| Feature | Status | Date |
|---------|--------|------|
| Person search (advanced) | ✅ DONE | May 6, 2026 |
| Person search (appearance) | ✅ DONE | May 6, 2026 |
| Person search (location-time) | ✅ DONE | May 6, 2026 |
| Vehicle search (advanced) | ✅ DONE | May 6, 2026 |
| Vehicle search (license plate) | ✅ DONE | May 6, 2026 |
| Vehicle search (type-color) | ✅ DONE | May 6, 2026 |
| Alert search (advanced) | ✅ DONE | May 6, 2026 |
| Alert search (type-severity) | ✅ DONE | May 6, 2026 |
| Alert search (active) | ✅ DONE | May 6, 2026 |
| Face search (embedding) | ✅ DONE | May 6, 2026 |
| Face search (by person) | ✅ DONE | May 6, 2026 |
| Face search (with embedding) | ✅ DONE | May 6, 2026 |

---

**Total**: 12 advanced search endpoints implemented ✅

**System Status**: 92% → **100% COMPLETE** 🎉

---

Last updated: May 6, 2026  
Historical search feature: **COMPLETED**
