"""
Test script to verify installation and basic functionality
"""

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    
    try:
        import cv2
        print("✓ OpenCV imported successfully")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ NumPy imported successfully")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    try:
        from paddleocr import PaddleOCR
        print("✓ PaddleOCR imported successfully")
    except ImportError as e:
        print(f"✗ PaddleOCR import failed: {e}")
        print("  Run: pip install paddleocr paddlepaddle")
        return False
    
    try:
        import re
        print("✓ Regex module available")
    except ImportError as e:
        print(f"✗ Regex import failed: {e}")
        return False
    
    print("\nAll imports successful! ✓")
    return True


def test_modules():
    """Test if custom modules can be imported"""
    print("\nTesting custom modules...")
    
    try:
        import config
        print("✓ config.py loaded")
    except Exception as e:
        print(f"✗ config.py failed: {e}")
        return False
    
    try:
        from preprocessing import VideoPreprocessor
        print("✓ preprocessing.py loaded")
    except Exception as e:
        print(f"✗ preprocessing.py failed: {e}")
        return False
    
    try:
        from ocr_module import TrainOCR
        print("✓ ocr_module.py loaded")
    except Exception as e:
        print(f"✗ ocr_module.py failed: {e}")
        return False
    
    try:
        from integration import TrainDetectionOCRPipeline
        print("✓ integration.py loaded")
    except Exception as e:
        print(f"✗ integration.py failed: {e}")
        return False
    
    print("\nAll custom modules loaded! ✓")
    return True


def test_basic_functionality():
    """Test basic pipeline functionality"""
    print("\nTesting basic functionality...")
    
    try:
        import numpy as np
        from preprocessing import VideoPreprocessor
        from ocr_module import TrainOCR
        from integration import TrainDetectionOCRPipeline
        
        # Create dummy frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Test preprocessor
        preprocessor = VideoPreprocessor()
        processed = preprocessor.preprocess_frame(frame)
        print("✓ Preprocessing works")
        
        # Test OCR initialization (might download models on first run)
        print("  Initializing OCR (may download models on first run, ~100MB)...")
        ocr = TrainOCR()
        print("✓ OCR initialized")
        
        # Test pipeline
        pipeline = TrainDetectionOCRPipeline()
        print("✓ Pipeline initialized")
        
        print("\nAll functionality tests passed! ✓")
        return True
        
    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("Train OCR Pipeline - Installation Test")
    print("="*60)
    print()
    
    # Run tests
    imports_ok = test_imports()
    if not imports_ok:
        print("\n" + "="*60)
        print("FAILED: Please install missing dependencies")
        print("Run: pip install -r requirements.txt")
        print("="*60)
        return
    
    modules_ok = test_modules()
    if not modules_ok:
        print("\n" + "="*60)
        print("FAILED: Custom modules have errors")
        print("="*60)
        return
    
    functionality_ok = test_basic_functionality()
    
    print("\n" + "="*60)
    if imports_ok and modules_ok and functionality_ok:
        print("SUCCESS! Everything is working correctly!")
        print("\nYou can now use the pipeline:")
        print("  python demo.py --video input.mp4 --output output.mp4")
    else:
        print("FAILED: Some tests did not pass")
    print("="*60)


if __name__ == "__main__":
    main()
