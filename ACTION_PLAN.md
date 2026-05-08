# 📋 ACTION PLAN - Camera Tracking AI Next Steps

**Priority**: Implement comprehensive search APIs  
**Timeline**: 1-2 weeks  
**Impact**: Enable full system functionality (92% → 100%)

---

## 🎯 PRIORITY 1: Implement Search APIs (1-2 weeks)

### Task 1.1: Person Search API
**File**: `app.py`  
**Status**: 🔴 TODO

```python
@app.route('/api/persons/search', methods=['POST'])
def search_persons():
    """
    Search persons by attributes
    
    Request:
    {
        "location": "cam_01",
        "start_time": "2026-05-06T08:00:00Z",
        "end_time": "2026-05-06T18:00:00Z",
        "shirt_color": "blue",           # Optional
        "pants_color": "black",          # Optional
        "hair_color": "black",           # Optional
        "confidence_min": 0.8,           # Optional
        "limit": 100                     # Optional
    }
    
    Response:
    {
        "total": 5,
        "results": [
            {
                "person_id": "person_123",
                "location": "cam_01",
                "timestamp": "2026-05-06T10:30:45Z",
                "shirt_colors": [...],
                "pants_colors": [...],
                "hair_colors": [...],
                "confidence": 0.92
            }
        ]
    }
    """
    data = request.json
    
    # Build query
    query = Person.query
    
    # Add filters
    if data.get('location'):
        query = query.filter_by(location=data['location'])
    
    if data.get('start_time'):
        start = datetime.fromisoformat(data['start_time'])
        query = query.filter(Person.timestamp >= start)
    
    if data.get('end_time'):
        end = datetime.fromisoformat(data['end_time'])
        query = query.filter(Person.timestamp <= end)
    
    if data.get('confidence_min'):
        query = query.filter(Person.confidence >= data['confidence_min'])
    
    # Color filters (JSON search)
    if data.get('shirt_color'):
        # Search JSON array for color name
        query = query.filter(
            Person.shirt_colors.astext.ilike(f"%{data['shirt_color']}%")
        )
    
    # Execute query
    limit = min(data.get('limit', 100), 1000)
    results = query.order_by(desc(Person.timestamp)).limit(limit).all()
    
    return jsonify({
        'total': len(results),
        'results': [p.to_dict() for p in results]
    })
```

**Estimated Time**: 3 hours

---

### Task 1.2: Vehicle Search API
**File**: `app.py`  
**Status**: 🔴 TODO

```python
@app.route('/api/vehicles/search', methods=['POST'])
def search_vehicles():
    """
    Search vehicles by attributes
    
    Request:
    {
        "vehicle_type": "car",
        "license_plate": "51A-12345",
        "vehicle_color": "white",
        "location": "cam_01",
        "start_time": "2026-05-06T08:00:00Z",
        "end_time": "2026-05-06T18:00:00Z",
        "confidence_min": 0.85,
        "limit": 50
    }
    """
    data = request.json
    
    query = Vehicle.query
    
    if data.get('vehicle_type'):
        query = query.filter_by(vehicle_type=data['vehicle_type'])
    
    if data.get('license_plate'):
        query = query.filter_by(license_plate=data['license_plate'])
    
    if data.get('location'):
        query = query.filter_by(location=data['location'])
    
    if data.get('start_time'):
        start = datetime.fromisoformat(data['start_time'])
        query = query.filter(Vehicle.timestamp >= start)
    
    if data.get('end_time'):
        end = datetime.fromisoformat(data['end_time'])
        query = query.filter(Vehicle.timestamp <= end)
    
    if data.get('vehicle_color'):
        query = query.filter(
            Vehicle.vehicle_colors.astext.ilike(f"%{data['vehicle_color']}%")
        )
    
    limit = min(data.get('limit', 100), 1000)
    results = query.order_by(desc(Vehicle.timestamp)).limit(limit).all()
    
    return jsonify({
        'total': len(results),
        'results': [v.to_dict() for v in results]
    })
```

**Estimated Time**: 2 hours

---

### Task 1.3: Alert Search API
**File**: `app.py`  
**Status**: 🔴 TODO

```python
@app.route('/api/alerts/search', methods=['POST'])
def search_alerts():
    """
    Search alerts by type, status, severity
    """
    data = request.json
    
    query = Alert.query
    
    if data.get('alert_type'):
        query = query.filter_by(alert_type=data['alert_type'])
    
    if data.get('status'):
        query = query.filter_by(status=data['status'])
    
    if data.get('severity'):
        query = query.filter_by(severity=data['severity'])
    
    if data.get('location'):
        query = query.filter_by(location=data['location'])
    
    if data.get('start_time'):
        start = datetime.fromisoformat(data['start_time'])
        query = query.filter(Alert.timestamp >= start)
    
    if data.get('end_time'):
        end = datetime.fromisoformat(data['end_time'])
        query = query.filter(Alert.timestamp <= end)
    
    limit = min(data.get('limit', 100), 1000)
    results = query.order_by(desc(Alert.timestamp)).limit(limit).all()
    
    return jsonify({
        'total': len(results),
        'results': [a.to_dict() for a in results]
    })
```

**Estimated Time**: 1.5 hours

---

### Task 1.4: Face Search (Vector Similarity)
**File**: `app.py`  
**Status**: 🟡 PARTIAL (need enhancement)

```python
@app.route('/api/faces/search', methods=['POST'])
def search_faces():
    """
    Search faces using embeddings (cosine similarity)
    
    Request:
    {
        "method": "similarity",  # or "exact"
        "embedding": [...],      # 512-dim float array
        "threshold": 0.6,        # Cosine similarity threshold
        "limit": 50
    }
    """
    from ai_engine.utils.face_matcher import get_face_matching_engine
    
    data = request.json
    embedding = np.array(data['embedding'], dtype=np.float32)
    threshold = data.get('threshold', 0.6)
    limit = min(data.get('limit', 50), 500)
    
    engine = get_face_matching_engine()
    
    # Find all persons with faces
    persons = Person.query.filter(Person.face_embedding.isnot(None)).all()
    
    matches = []
    for person in persons:
        if person.face_embedding:
            stored_embedding = np.array(person.face_embedding, dtype=np.float32)
            # Cosine similarity
            similarity = np.dot(embedding, stored_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(stored_embedding)
            )
            
            if similarity >= threshold:
                matches.append({
                    'person_id': person.person_id,
                    'similarity': float(similarity),
                    'location': person.location,
                    'timestamp': person.timestamp.isoformat(),
                    'confidence': person.confidence
                })
    
    # Sort by similarity desc
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    
    return jsonify({
        'total': len(matches),
        'results': matches[:limit]
    })
```

**Estimated Time**: 2 hours

---

## 🎯 PRIORITY 2: Face ID Management APIs (3-4 days)

### Task 2.1: Register Known Face
**File**: `app.py`  
**Status**: 🔴 TODO

```python
@app.route('/api/known-faces', methods=['POST'])
def register_known_face():
    """
    Register a known person's face
    
    Request:
    {
        "name": "Nguyễn Văn A",
        "embedding": [...],      # 512-dim
        "metadata": {
            "age": 35,
            "gender": "M",
            "department": "Sales"
        }
    }
    """
    from ai_engine.utils.face_matcher import get_face_matching_engine
    
    data = request.json
    
    # Generate person_id
    person_id = f"known_{uuid.uuid4().hex[:8]}"
    
    # Store in known_faces
    engine = get_face_matching_engine()
    engine.add_known_face(
        person_id=person_id,
        embedding=data['embedding'],
        metadata={
            'name': data.get('name'),
            **data.get('metadata', {})
        }
    )
    
    return jsonify({
        'person_id': person_id,
        'name': data.get('name'),
        'status': 'registered'
    }), 201
```

**Estimated Time**: 2 hours

---

### Task 2.2: List Known Faces
**File**: `app.py`  
**Status**: 🔴 TODO

```python
@app.route('/api/known-faces', methods=['GET'])
def list_known_faces():
    """List all registered known faces"""
    from ai_engine.utils.face_matcher import get_face_matching_engine
    
    engine = get_face_matching_engine()
    
    results = []
    for person_id, face_data in engine.known_faces.items():
        results.append({
            'person_id': person_id,
            'metadata': face_data.get('metadata'),
            'added_at': face_data.get('added_at'),
            'match_count': face_data.get('match_count', 0)
        })
    
    return jsonify({
        'total': len(results),
        'results': results
    })
```

**Estimated Time**: 1 hour

---

### Task 2.3: Delete Known Face
**File**: `app.py`  
**Status**: 🔴 TODO

```python
@app.route('/api/known-faces/<person_id>', methods=['DELETE'])
def delete_known_face(person_id):
    """Remove a known person"""
    from ai_engine.utils.face_matcher import get_face_matching_engine
    
    engine = get_face_matching_engine()
    
    if person_id in engine.known_faces:
        del engine.known_faces[person_id]
        engine._save_known_faces()  # Persist
        return jsonify({'status': 'deleted'})
    else:
        return jsonify({'error': 'Not found'}), 404
```

**Estimated Time**: 0.5 hours

---

### Task 2.4: Search by Image
**File**: `app.py`  
**Status**: 🟡 PARTIAL

```python
@app.route('/api/faces/search-image', methods=['POST'])
def search_face_by_image():
    """
    Search for matching person from uploaded image
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    img_data = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
    
    # Extract face embedding
    from ai_engine.processors.face_processor import FaceProcessor
    processor = FaceProcessor()
    result = processor.process(img)
    
    if not result['faces']:
        return jsonify({'error': 'No face detected'}), 400
    
    face_embedding = np.array(result['faces'][0]['embedding'])
    threshold = request.form.get('threshold', 0.6, type=float)
    
    # Search in known faces
    from ai_engine.utils.face_matcher import get_face_matching_engine
    engine = get_face_matching_engine()
    
    matches = []
    for person_id, face_data in engine.known_faces.items():
        stored_emb = np.array(face_data['embedding'])
        similarity = np.dot(face_embedding, stored_emb) / (
            np.linalg.norm(face_embedding) * np.linalg.norm(stored_emb)
        )
        
        if similarity >= threshold:
            matches.append({
                'person_id': person_id,
                'similarity': float(similarity),
                'metadata': face_data.get('metadata')
            })
    
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    
    return jsonify({
        'matches': matches,
        'detected_faces': len(result['faces'])
    })
```

**Estimated Time**: 2 hours

---

## 🎯 PRIORITY 3: Optional Enhancements (2 weeks)

### Task 3.1: Install pgvector for Vector Search
```bash
# Install pgvector PostgreSQL extension
# Enables: SELECT * FROM persons WHERE face_embedding <-> $1 < 0.3

# Steps:
1. Connect to PostgreSQL
2. CREATE EXTENSION IF NOT EXISTS vector;
3. Alter table persons ADD COLUMN embedding_pgvector vector(512);
4. CREATE INDEX ON persons USING ivfflat (embedding_pgvector vector_cosine_ops);
```

**Effort**: 1-2 hours

---

### Task 3.2: Frontend Search Interface
**Status**: 🔴 TODO

Create React component for:
- Date/time range picker
- Color selector (dropdown)
- Vehicle type filter
- Location (camera) selector
- Results table with pagination
- Image upload for face search

**Effort**: 3-4 days

---

### Task 3.3: Dashboard Enhancements
- Real-time detection map
- Alert heatmap
- Timeline view (Gantt chart)
- Statistics dashboard

**Effort**: 1 week

---

## 📊 IMPLEMENTATION TIMELINE

```
Week 1:
├─ Day 1-2: Person search API (Task 1.1)
├─ Day 2-3: Vehicle search API (Task 1.2)
├─ Day 3-4: Alert search API (Task 1.3)
└─ Day 4-5: Face search enhancement (Task 1.4)

Week 2:
├─ Day 1-2: Face ID management APIs (Tasks 2.1-2.4)
├─ Day 3-4: Testing & bug fixes
└─ Day 5: Deployment to staging

Week 3 (Optional):
├─ Day 1-2: pgvector integration
├─ Day 3-5: Frontend search UI
└─ Testing

Week 4 (Optional):
├─ Dashboard enhancements
└─ Production deployment
```

---

## ✅ TESTING CHECKLIST

- [ ] Person search with all filters
- [ ] Vehicle search with all filters
- [ ] Alert search functionality
- [ ] Face embedding search accuracy
- [ ] Known face registration/deletion
- [ ] Image upload face search
- [ ] Large dataset performance (>10k records)
- [ ] Error handling & edge cases
- [ ] API documentation

---

## 📚 RELATED FILES

| File | Purpose | Status |
|---|---|---|
| `app.py` | Main Flask app | ✅ Need updates |
| `models.py` | Database models | ✅ Complete |
| `ai_engine/utils/face_matcher.py` | Face matching | ✅ Complete |
| `requirements.txt` | Dependencies | ✅ Complete |
| `README.md` | Documentation | ⚠️ Needs update |

---

**Last Updated**: May 6, 2026  
**Status**: Ready for implementation
