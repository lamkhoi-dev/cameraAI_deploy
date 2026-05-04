# 🚀 FaceID Quick Reference Card

**Phase 2 Implementation - Complete**

---

## ⚡ 5-Minute Setup

```bash
# 1. Install (1 min)
pip install insightface onnxruntime

# 2. Enable config (30 sec)
# Edit ai_engine/config.py:
# USE_FACE_DETECTION = True
# USE_FACE_RECOGNITION = True

# 3. Start (30 sec)
python app.py

# 4. Test (1 min)
python test_faceid.py

# 5. Open dashboard
# http://localhost:5000/dashboard
```

---

## 📝 API Cheat Sheet

### Register Face
```bash
# From image file
curl -X POST http://localhost:5000/api/faces/register-image \
  -F "image=@face.jpg" \
  -F "person_id=john_001" \
  -F 'metadata={"name": "John Doe"}'

# From embedding (512-dim)
curl -X POST http://localhost:5000/api/faces/known \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "employee_1",
    "embedding": [0.1, 0.2, ..., 0.5],
    "metadata": {"name": "John Doe"}
  }'
```

### Search Face
```bash
# From image file
curl -X POST http://localhost:5000/api/faces/search-image \
  -F "image=@unknown.jpg"

# From embedding (512-dim)
curl -X POST http://localhost:5000/api/faces/match \
  -H "Content-Type: application/json" \
  -d '{"embedding": [0.1, 0.2, ..., 0.5]}'
```

### Manage Database
```bash
# Get all known faces
curl http://localhost:5000/api/faces/known

# Get statistics
curl http://localhost:5000/api/faces/stats

# Remove a face
curl -X DELETE http://localhost:5000/api/faces/known/john_001

# Get persons with faces
curl "http://localhost:5000/api/faces/persons-with-faces"

# Get person history
curl "http://localhost:5000/api/faces/person/john_001/history"
```

---

## 🔧 Configuration

```python
# ai_engine/config.py

# Model choice (speed vs accuracy)
FACE_EMBEDDING_MODEL = "buffalo_l"    # Options: buffalo_s, buffalo_m, buffalo_l

# Matching threshold
FACE_SIMILARITY_THRESHOLD = 0.6       # 0.5=loose, 0.6=balanced, 0.7=strict

# Detection
FACE_DETECTION_CONFIDENCE = 0.5       # Higher = stricter
FACE_MIN_FACE_SIZE = 10               # Minimum pixels

# Enable features
USE_FACE_DETECTION = True
USE_FACE_RECOGNITION = True
```

---

## 📊 Quick Reference

| Config | Value | Effect |
|--------|-------|--------|
| `FACE_SIMILARITY_THRESHOLD` | 0.5 | Loose matching |
| | 0.6 | Balanced (default) |
| | 0.7 | Strict matching |
| `FACE_EMBEDDING_MODEL` | `buffalo_s` | Fast (10MB) |
| | `buffalo_m` | Balanced (20MB) |
| | `buffalo_l` | Accurate (40MB) ← Default |

---

## ⚡ Workflow Example

```bash
# 1. Register John
curl -X POST http://localhost:5000/api/faces/register-image \
  -F "image=@john.jpg" \
  -F "person_id=john_001"

# 2. Register Jane
curl -X POST http://localhost:5000/api/faces/register-image \
  -F "image=@jane.jpg" \
  -F "person_id=jane_001"

# 3. Search unknown person
curl -X POST http://localhost:5000/api/faces/search-image \
  -F "image=@unknown.jpg"

# 4. Get statistics
curl http://localhost:5000/api/faces/stats
```

---

## 🔍 API Response Examples

**Match Found:**
```json
{
  "status": "matched",
  "person_id": "john_001",
  "similarity": 0.87,
  "confidence_percent": 87.0
}
```

**No Match:**
```json
{
  "status": "no_match",
  "message": "No matching face found"
}
```

---

## ✅ Troubleshooting

| Problem | Solution |
|---------|----------|
| Module not found | `pip install insightface onnxruntime` |
| Face not detected | Use clear frontal face image |
| Low accuracy | Increase FACE_SIMILARITY_THRESHOLD to 0.7 |
| Slow inference | Use `buffalo_s` instead of `buffalo_l` |
| Connection error | Make sure `python app.py` is running |

---

## 📚 Documentation

- **Full Guide**: `FACEID_IMPLEMENTATION_GUIDE.md` (500+ lines)
- **Summary**: `FACEID_IMPLEMENTATION_SUMMARY.md`
- **Tests**: `python test_faceid.py`
- **Source**: `ai_engine/processors/face_processor.py`

---

## 📞 Quick Links

- Test Suite: `python test_faceid.py`
- Dashboard: http://localhost:5000/dashboard
- API Health: http://localhost:5000/health
- Statistics: http://localhost:5000/api/faces/stats

---

**Last Updated**: May 4, 2026  
**Status**: ✅ Production Ready


## 📚 More Information

See [FACEID_IMPLEMENTATION.md](FACEID_IMPLEMENTATION.md) for:
- Complete API reference
- Advanced configuration
- Performance tuning
- Troubleshooting guide
- Integration examples

---

**Status**: ✅ Ready to Use  
**Next**: Try [FaceID Examples](#examples)

---

## 📝 Examples

### Example 1: Register Employee
```python
import requests

# Extract embedding from employee photo (done by AI engine)
embedding = [0.1, 0.2, ..., 0.5]  # 512-dim

# Register
response = requests.post(
    'http://localhost:8000/api/faces/known',
    json={
        'person_id': 'emp_001',
        'embedding': embedding,
        'metadata': {
            'name': 'Alice Smith',
            'role': 'Manager',
            'department': 'Security'
        }
    }
)

print(response.json())
# {"status": "registered", "person_id": "emp_001"}
```

### Example 2: Match Face
```python
# When a face is detected
match = requests.post(
    'http://localhost:8000/api/faces/match',
    json={'embedding': detected_embedding}
)

result = match.json()

if result['status'] == 'matched':
    print(f"Found: {result['person_id']} ({result['similarity']:.1%})")
else:
    print("Unknown person")
```

### Example 3: List All Registered People
```python
response = requests.get('http://localhost:8000/api/faces/known')
data = response.json()

print(f"Total registered: {data['total']}")

for person_id, info in data['faces'].items():
    print(f"- {info['metadata']['name']} (matches: {info['match_count']})")
```

---

**Ready!** Your FaceID system is now fully operational. 🎯
