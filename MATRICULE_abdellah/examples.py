"""
Example script showing different usage scenarios
"""

import cv2
import numpy as np
from integration import TrainDetectionOCRPipeline, DetectionOCRInterface
from preprocessing import VideoPreprocessor
from ocr_module import TrainOCR


def example_1_basic_usage():
    """
    Example 1: Basic image processing
    """
    print("\n" + "="*60)
    print("Example 1: Basic Image Processing")
    print("="*60)
    
    # Create or load an image
    # frame = cv2.imread('train_image.jpg')
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Initialize interface
    interface = DetectionOCRInterface()
    
    # Process frame (without pre-computed detections)
    results = interface.detect_and_read(frame)
    
    # Display results
    print(f"Found {len(results)} wagon(s):")
    for result in results:
        print(f"  - Wagon ID: {result['wagon_id']}")
        print(f"    Confidence: {result['confidence']:.2f}")
        print(f"    Position: {result['bbox']}")
    
    # Export results
    interface.export_results(results, 'results_example1.json')
    print("\nResults exported to: results_example1.json")


def example_2_with_detection():
    """
    Example 2: Integration with existing detection system
    """
    print("\n" + "="*60)
    print("Example 2: Integration with Detection System")
    print("="*60)
    
    # Simulate frame
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Simulate detections from Membre 1 (YOLOv8 output)
    detections = [
        {
            'bbox': (100, 150, 200, 100),  # (x, y, width, height)
            'class': 'train',
            'confidence': 0.95
        },
        {
            'bbox': (350, 200, 180, 90),
            'class': 'train',
            'confidence': 0.88
        }
    ]
    
    # Initialize pipeline
    pipeline = TrainDetectionOCRPipeline()
    
    # Process with detections
    annotated, ocr_results = pipeline.process_frame(frame, detections)
    
    print(f"Processed {len(detections)} detections")
    print(f"OCR successful on {len(ocr_results)} wagon(s)")
    
    # Save annotated frame
    # cv2.imwrite('annotated_example2.jpg', annotated)


def example_3_custom_preprocessing():
    """
    Example 3: Custom preprocessing pipeline
    """
    print("\n" + "="*60)
    print("Example 3: Custom Preprocessing")
    print("="*60)
    
    # Load frame
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Initialize preprocessor
    preprocessor = VideoPreprocessor()
    
    # Define custom perspective points
    # These should be adjusted based on your camera setup
    h, w = frame.shape[:2]
    perspective_points = np.float32([
        [w * 0.1, h * 0.3],  # Top-left
        [w * 0.9, h * 0.3],  # Top-right
        [w * 0.95, h * 0.9], # Bottom-right
        [w * 0.05, h * 0.9]  # Bottom-left
    ])
    
    # Apply preprocessing with custom points
    processed = preprocessor.preprocess_frame(frame, perspective_points)
    
    print(f"Original shape: {frame.shape}")
    print(f"Processed shape: {processed.shape}")
    
    # Save result
    # cv2.imwrite('preprocessed_example3.jpg', processed)


def example_4_video_processing():
    """
    Example 4: Complete video processing
    """
    print("\n" + "="*60)
    print("Example 4: Video Processing")
    print("="*60)
    
    # This is a template - replace with actual video path
    input_video = "input_video.mp4"
    output_video = "output_annotated.mp4"
    
    print(f"To process a video, use:")
    print(f"  pipeline.process_video('{input_video}', '{output_video}')")
    print(f"\nOr use the demo script:")
    print(f"  python demo.py --video {input_video} --output {output_video}")


def example_5_custom_validation():
    """
    Example 5: Custom wagon ID validation
    """
    print("\n" + "="*60)
    print("Example 5: Custom Validation Logic")
    print("="*60)
    
    from ocr_module import TrainOCR
    import config
    
    # Initialize OCR
    ocr = TrainOCR()
    
    # Test different formats
    test_ids = [
        "AB-12345",
        "SNCF-123456",
        "1234567",
        "INVALID",
        "XY 9999",
    ]
    
    print(f"Current pattern: {config.WAGON_ID_PATTERN}")
    print("\nValidation results:")
    
    for wagon_id in test_ids:
        is_valid = ocr.validate_wagon_id(wagon_id)
        cleaned = ocr.clean_text(wagon_id)
        status = "✓" if is_valid else "✗"
        print(f"  {status} {wagon_id:15} -> {cleaned:15} (valid: {is_valid})")
    
    print("\nTo customize validation:")
    print("  1. Edit WAGON_ID_PATTERN in config.py")
    print("  2. Modify clean_text() in ocr_module.py for corrections")


def example_6_batch_processing():
    """
    Example 6: Batch processing multiple images
    """
    print("\n" + "="*60)
    print("Example 6: Batch Processing")
    print("="*60)
    
    # Initialize interface
    interface = DetectionOCRInterface()
    
    # Simulate multiple frames
    frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(5)]
    
    all_results = []
    
    print("Processing batch...")
    for i, frame in enumerate(frames):
        results = interface.detect_and_read(frame)
        all_results.extend(results)
        print(f"  Frame {i+1}: {len(results)} detections")
    
    print(f"\nTotal detections: {len(all_results)}")
    
    # Get unique wagon IDs
    unique_wagons = set(r['wagon_id'] for r in all_results)
    print(f"Unique wagons: {len(unique_wagons)}")


def main():
    """
    Run all examples
    """
    print("="*60)
    print("Train OCR Pipeline - Usage Examples")
    print("="*60)
    
    print("\nThese examples demonstrate different usage scenarios.")
    print("Most examples use dummy data. Replace with your actual data.")
    
    try:
        example_1_basic_usage()
        example_2_with_detection()
        example_3_custom_preprocessing()
        example_4_video_processing()
        example_5_custom_validation()
        example_6_batch_processing()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
