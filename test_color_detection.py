#!/usr/bin/env python3
"""
Test Color Detection - Kiểm tra hiệu suất nhận diện màu sắc
"""

import cv2
import numpy as np
from pathlib import Path
from ai_engine.utils.color_analyzer import ColorAnalyzer
import argparse
from datetime import datetime


def test_color_detection(image_path: str, num_colors: int = 3, margin_ratio: float = 0.15):
    """
    Test color detection trên một ảnh
    
    Args:
        image_path: Đường dẫn tới ảnh
        num_colors: Số lượng màu chính
        margin_ratio: Tỉ lệ crop nền
    """
    # Load ảnh
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Không thể load ảnh: {image_path}")
        return
    
    print(f"\n📸 Testing Color Detection")
    print(f"{'='*50}")
    print(f"📁 Ảnh: {image_path}")
    print(f"📐 Kích thước: {img.shape}")
    print(f"🎛️ Tham số: num_colors={num_colors}, margin={margin_ratio}")
    print(f"⏱️ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Khởi tạo analyzer
    analyzer = ColorAnalyzer(num_colors=num_colors, margin_ratio=margin_ratio)
    
    # Analyze
    import time
    start = time.time()
    colors = analyzer.analyze(img, part_name="test_image")
    elapsed = time.time() - start
    
    print(f"⏱️ Thời gian xử lý: {elapsed*1000:.2f}ms")
    print(f"\n🎨 Kết Quả Nhận Diện Màu:")
    print(f"{'-'*50}")
    
    if colors is None:
        print("❌ Không thể phân tích ảnh")
        return
    
    for color in colors:
        bar = "█" * (color['rank'] * 5)
        print(f"  #{color['rank']}: {color['name']:<15} {bar}")
        print(f"       RGB: {color['rgb']}")
        print(f"       HSV: {color['hsv']}")
        print()
    
    # Hiển thị ảnh gốc + ảnh sau enhance
    print(f"\n📊 Visualizations:")
    print(f"  - Nhấn ESC để thoát")
    
    # Áp dụng CLAHE để so sánh
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    lab_enhanced = cv2.merge([l_enhanced, a, b])
    img_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
    
    # Hiển thị side-by-side
    h, w = img.shape[:2]
    comparison = np.hstack([img, img_enhanced])
    
    # Resize nếu quá lớn
    if comparison.shape[1] > 1200:
        scale = 1200 / comparison.shape[1]
        comparison = cv2.resize(comparison, None, fx=scale, fy=scale)
    
    cv2.imshow("Left: Original | Right: Enhanced (CLAHE)", comparison)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def batch_test(folder_path: str):
    """Test color detection trên toàn bộ ảnh trong folder"""
    folder = Path(folder_path)
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    images = []
    for ext in image_extensions:
        images.extend(folder.glob(f"*{ext}"))
        images.extend(folder.glob(f"*{ext.upper()}"))
    
    if not images:
        print(f"❌ Không tìm thấy ảnh trong: {folder_path}")
        return
    
    print(f"\n🔍 Tìm thấy {len(images)} ảnh")
    print(f"{'='*50}\n")
    
    results = []
    for i, img_path in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}] {img_path.name}")
        try:
            img = cv2.imread(str(img_path))
            analyzer = ColorAnalyzer(num_colors=3)
            
            import time
            start = time.time()
            colors = analyzer.analyze(img)
            elapsed = time.time() - start
            
            if colors:
                top_color = colors[0]['name']
                print(f"  ✅ Màu chính: {top_color} ({elapsed*1000:.1f}ms)")
                results.append({
                    'image': img_path.name,
                    'color': top_color,
                    'time': elapsed
                })
            else:
                print(f"  ⚠️  Không thể phân tích")
        except Exception as e:
            print(f"  ❌ Lỗi: {e}")
    
    # Summary
    if results:
        print(f"\n\n📊 SUMMARY")
        print(f"{'='*50}")
        print(f"Tổng ảnh xử lý: {len(results)}")
        avg_time = sum(r['time'] for r in results) / len(results)
        print(f"Thời gian trung bình: {avg_time*1000:.2f}ms")
        print(f"\nPhân bố màu chính:")
        from collections import Counter
        color_dist = Counter(r['color'] for r in results)
        for color, count in color_dist.most_common():
            print(f"  {color}: {count} ảnh")


def main():
    parser = argparse.ArgumentParser(
        description="Test Color Detection - Kiểm tra nhận diện màu sắc"
    )
    parser.add_argument(
        "--image", "-i",
        help="Đường dẫn tới ảnh để test"
    )
    parser.add_argument(
        "--folder", "-f",
        help="Thư mục chứa ảnh để test batch"
    )
    parser.add_argument(
        "--num-colors", "-n",
        type=int,
        default=3,
        help="Số lượng màu chính (default: 3)"
    )
    parser.add_argument(
        "--margin", "-m",
        type=float,
        default=0.15,
        help="Tỉ lệ crop nền (default: 0.15)"
    )
    
    args = parser.parse_args()
    
    if args.image:
        test_color_detection(args.image, args.num_colors, args.margin)
    elif args.folder:
        batch_test(args.folder)
    else:
        # Test trên ảnh mặc định nếu có
        default_image = Path("cropped_data/person_2/frame_001.jpg")
        if default_image.exists():
            test_color_detection(str(default_image))
        else:
            print("❌ Vui lòng cung cấp --image hoặc --folder")
            print(f"   Ví dụ: python test_color_detection.py --image image.jpg")
            print(f"   Hoặc: python test_color_detection.py --folder cropped_data/person_2/")


if __name__ == "__main__":
    main()
